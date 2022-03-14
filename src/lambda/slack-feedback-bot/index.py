import json
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from database import Database
from helpers import create_feedback_blocks

# Initializes your app with your bot token and socket mode handler
app = App(process_before_response=True)
db = Database()


@app.command('/feedback_loop')
def feedback(ack, body, client):
    print(f'Feedback loop with body: {body}')
    ack()
    user_id = body["user_id"]
    channel_id = body["channel_id"]

    print(f'Sending feedback loop options for {user_id} in {channel_id}')
    client.chat_postEphemeral(
        channel=channel_id,
        user=user_id,
        text=f"Manage Feedback Loops",
        blocks=[
            {
                "type": "section", "text": {"type": "mrkdwn", "text": f":gear: *Manage Feedback Loops*"},
            },
            {
                "type": "actions",
                "block_id": "setup_button",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "setup_feedback_loop",
                        "text": {
                            "type": "plain_text",
                            "text": "Create Feedback Loop",
                        },
                        "style": "primary",
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "edit_button",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "edit_feedback_loop",
                        "text": {
                            "type": "plain_text",
                            "text": "Edit Feedback Loop",
                        },
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": "delete_button",
                "elements": [
                    {
                        "type": "button",
                        "action_id": "delete_feedback_loop",
                        "text": {
                            "type": "plain_text",
                            "text": "Delete Feedback Loop",
                        },
                        "style": "danger",
                    }
                ]
            }
        ]
    )


@app.action('setup_feedback_loop')
@app.command('/setup_feedback_loop')
def setup_feedback(ack, body, client):
    print(f'Setting up feedback loop with body: {body}')
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            # View identifier
            "callback_id": "feedback_setup_view",
            "title": {"type": "plain_text", "text": "Feedback Loop Setup"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "team_block",
                    "label": {"type": "plain_text", "text": "Enter your team name."},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "team_input"
                    }
                },
                {
                    "type": "section",
                    "block_id": "multi_users_select_section",
                    "text": {"type": "plain_text", "text": "Who is in the team?"},
                    "accessory": {
                        "action_id": "setup_users",
                        "type": "multi_users_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select users"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "frequency_block",
                    "label": {"type": "plain_text", "text": "How often do you want this to occur?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "frequency_input",
                        "placeholder": {"type": "plain_text", "text": "AWS Cron Expression. I.e. 0 20 ? * MON * "}
                    }
                },
                {
                    "type": "section",
                    "block_id": "master_channel_section",
                    "text": {"type": "plain_text", "text": "Pick channels to send all feedback to"},
                    "accessory": {
                        "action_id": "master_channels_select",
                        "type": "multi_conversations_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select channels"
                        }
                    }
                }
            ]
        }
    )


@app.view('feedback_setup_view')
def setup_feedback_view(ack, view, client):
    ack()
    print(f'Creating feedback loop in DynamoDB with values: {view["state"]["values"]}')
    team_name = view["state"]["values"]["team_block"]["team_input"]["value"]
    team = {
        'team': team_name,
        'sk': 'team',
        'members': view["state"]["values"]["multi_users_select_section"]["setup_users"]["selected_users"],
        'master_channels': view["state"]["values"]["master_channel_section"]["master_channels_select"]["selected_conversations"],
        'frequency': view["state"]["values"]["frequency_block"]["frequency_input"]["value"],
        'feedback_count': 0,
    }
    upsert_team(client, team)


def upsert_team(client, team):
    updated_members = db.get_updated_team_members(team)
    print(f'Updating team {team} with members {updated_members}')
    db.put_item(team)
    for member in updated_members:
        if member['type'] in ('new', 'existing'):
            db.put_item({
                'team': team['team'],
                'sk': 'user#' + member['id'],
                'completed_feedback': True
            })
        else:
            db.delete_item({
                'team': team['team'],
                'sk': 'user#' + member['id']
            })

        if member['type'] == 'new':
            client.chat_postMessage(
                channel=member['id'],
                text=f"You have been added to the feedback loop for *{team['team']}*. You will now receive feedback requests to"
                     f" fill out for your teammates.",
            )
        elif member['type'] == 'existing':
            client.chat_postMessage(
                channel=member['id'],
                text=f"The feedback loop for *{team['team']}* has been updated."
            )
        else:
            client.chat_postMessage(
                channel=member['id'],
                text=f"You have been removed from the feedback loop for *{team['team']}*"
            )


@app.action('edit_feedback_loop')
def edit_feedback(ack, body, client):
    print(f'Editing feedback loop with body: {body}')
    teams = db.get_all_teams()
    team_options = [{
        "text": {"type": "plain_text", "text": team['team']},
        "value": team['team']
    } for team in teams['Items']]

    ack()
    if team_options:
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "feedback_setup_view",
                "title": {"type": "plain_text", "text": "Edit a feedback loop"},
                "blocks": [
                    {
                        "type": "section",
                        "block_id": "delete_team_block",
                        "text": {"type": "plain_text", "text": "Pick a team to edit"},
                        "accessory": {
                            "action_id": "edit_team_select",
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a team"
                            },
                            "options": team_options
                        }
                    }
                ]
            }
        )
    else:
        client.chat_postEphemeral(
            channel=body['channel_id'],
            user=body['user_id'],
            text='No teams to delete.'
        )


@app.action('edit_team_select')
def edit_team_select(ack, body, client):
    ack()
    print(f'Editing team with body: {body}')
    selected_team_name = body['actions'][0]['selected_option']['value']
    team = db.get_team(selected_team_name)['Item']
    options = body["view"]["blocks"][0]["accessory"]["options"]
    print(f'Updating view with team: {team}')
    client.views_update(
        # Pass the view_id
        view_id=body["view"]["id"],
        # String that represents view state to protect against race conditions
        hash=body["view"]["hash"],
        # View payload with updated blocks
        view={
            "type": "modal",
            # View identifier
            "callback_id": "feedback_edit_view",
            "title": {"type": "plain_text", "text": f"Edit a feedback loop"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "section",
                    "block_id": "delete_team_block",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Selected team:*"},
                        {"type": "plain_text", "text": selected_team_name}
                    ]
                },
                {
                    "type": "section",
                    "block_id": "multi_users_select_section",
                    "text": {"type": "plain_text", "text": "Who is in the team?"},
                    "accessory": {
                        "action_id": "setup_users",
                        "type": "multi_users_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select users"
                        },
                        "initial_users": team['members']
                    },
                },
                {
                    "type": "input",
                    "block_id": "frequency_block",
                    "label": {"type": "plain_text", "text": "How often do you want this to occur?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "frequency_input",
                        "placeholder": {"type": "plain_text", "text": "AWS Cron Expression. I.e. 0 20 ? * MON * "},
                        "initial_value": team['frequency']
                    }
                },
                {
                    "type": "section",
                    "block_id": "master_channel_section",
                    "text": {"type": "plain_text", "text": "Pick channels to send all feedback to"},
                    "accessory": {
                        "action_id": "master_channels_select",
                        "type": "multi_conversations_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select channels"
                        },
                        "initial_conversations": team['master_channels']
                    }
                }
            ]
        }
    )


@app.view('feedback_edit_view')
def edit_feedback_view(ack, view, client):
    ack()
    print(f'Editing feedback loop in DynamoDB with values: {view}')
    team_name = view["blocks"][0]["fields"][1]["text"]
    team = {
        'team': team_name,
        'sk': 'team',
        'members': view["state"]["values"]["multi_users_select_section"]["setup_users"]["selected_users"],
        'master_channels': view["state"]["values"]["master_channel_section"]["master_channels_select"]["selected_conversations"],
        'frequency': view["state"]["values"]["frequency_block"]["frequency_input"]["value"],
        'feedback_count': 0,
    }
    upsert_team(client, team)


@app.action('delete_feedback_loop')
@app.command('/delete_feedback_loop')
def delete_feedback(ack, body, client):
    print(f'Deleting feedback loop with body: {body}')
    teams = db.get_all_teams()
    team_options = [{
        "text": {"type": "plain_text", "text": team['team']},
        "value": team['team']
    } for team in teams['Items']]

    ack()
    if team_options:
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "feedback_delete_view",
                "title": {"type": "plain_text", "text": "Delete a feedback loop"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "blocks": [
                    {
                        "type": "section",
                        "block_id": "delete_team_block",
                        "text": {"type": "plain_text", "text": "Pick a team to delete"},
                        "accessory": {
                            "action_id": "delete_team_select",
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a team"
                            },
                            "options": team_options
                        }
                    }
                ]
            }
        )
    else:
        client.chat_postEphemeral(
            channel=body['channel_id'],
            user=body['user_id'],
            text='No teams to delete.'
        )


@app.view('feedback_delete_view')
def delete_feedback_view(ack, view, client):
    ack()
    print(f'Deleting feedback loop in DynamoDB with values: {view["state"]["values"]}')
    team_name = view["state"]["values"]["delete_team_block"]["delete_team_select"]["selected_option"]["value"]
    team = db.get_team(team_name)
    for member in team['Item']['members']:
        db.delete_item({
            'team': team_name,
            'sk': 'user#' + member
        })
        client.chat_postMessage(
            channel=member,
            text=f"The feedback loop for *{team_name}* has been deleted.",
        )
    db.delete_item({'team': team_name, 'sk': 'team'})


@app.action("master_channels_select")
@app.action("delete_team_select")
@app.action("setup_users")
@app.action("user")
def handle_user_select(ack):
    ack()


@app.action('open_feedback')
def open_feedback(ack, body, client):
    print(f'Opening feedback form with body: {body}')
    ack()
    values = json.loads(body['actions'][0]['value'])
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "feedback_view",
            "title": {"type": "plain_text", "text": "Feedback Form"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "private_metadata": json.dumps(values),
            "blocks": [
                {
                    "type": "section",
                    "block_id": "users_select_section",
                    "text": {"type": "mrkdwn", "text": f"*Send feedback to <@{values['from_user_id']}>*"},
                },
                {
                    "type": "input",
                    "block_id": "input",
                    "label": {"type": "plain_text", "text": values['question']},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "feedback_input",
                        "multiline": True
                    }
                }
            ]
        }
    )


@app.view('feedback_view')
def handle_feedback(ack, body, client, view):
    print(f'Sending feedback with values: {view["state"]["values"]}')
    ack()
    values = json.loads(view["private_metadata"])

    user_id = body["user"]["id"]
    selected_user_id = values['from_user_id']
    question = values['question']
    master_channels = values['master_channels']
    text = view["state"]["values"]["input"]["feedback_input"]["value"]

    client.chat_postMessage(
        channel=user_id,
        text=f"Your feedback copy to <@{selected_user_id}>\n\n{question}\n\n{text}",
        blocks=create_feedback_blocks(f'Your feedback copy to <@{selected_user_id}>', question, text)
    )
    client.chat_postMessage(
        channel=selected_user_id,
        text=f"Your feedback from <@{user_id}>\n\n{question}\n\n{text}",
        blocks=create_feedback_blocks(f'Your feedback from <@{user_id}>', question, text)
    )
    for channel in master_channels:
        client.chat_postMessage(
            channel=channel,
            text=f"Feedback from <@{user_id}> to <@{selected_user_id}>",
            blocks=create_feedback_blocks(f'Feedback from <@{user_id}> to <@{selected_user_id}>', question, text)
        )

    db.put_item({
        'team': values['team'],
        'sk': f'user#{user_id}',
        'completed_feedback': True
    })


@app.command("/send_feedback")
def open_feedback_manual(ack, body, client):
    print(f'Opening manual feedback form with body: {body}')
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "feedback_view_manual",
            "title": {"type": "plain_text", "text": "Feedback Form"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "section",
                    "block_id": "users_select_section",
                    "text": {"type": "mrkdwn", "text": "*Send feedback to*"},
                    "accessory": {
                        "action_id": "user",
                        "type": "users_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a user"
                        }
                    }
                },
                {
                    "type": "input",
                    "block_id": "input",
                    "label": {"type": "plain_text", "text": "Enter your feedback"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "feedback_input",
                        "multiline": True
                    }
                }
            ]
        }
    )


@app.view('feedback_view_manual')
def handle_feedback_manual(ack, body, client, view):
    print(f'Sending manual feedback with values: {view["state"]["values"]}')
    ack()

    user_id = body["user"]["id"]
    selected_user_id = view["state"]["values"]["users_select_section"]["user"]["selected_user"]
    text = view["state"]["values"]["input"]["feedback_input"]["value"]

    client.chat_postMessage(
        channel=user_id,
        text=f"Your feedback copy to <@{selected_user_id}>\n\n{text}",
        blocks=create_feedback_blocks(f'Your feedback copy to <@{selected_user_id}>', response=text)
    )
    client.chat_postMessage(
        channel=selected_user_id,
        text=f"Your feedback from <@{user_id}>\n\n{text}",
        blocks=create_feedback_blocks(f'Your feedback from <@{user_id}>', response=text)
    )


def lambda_handler(event, context):
    return SlackRequestHandler(app=app).handle(event, context)
