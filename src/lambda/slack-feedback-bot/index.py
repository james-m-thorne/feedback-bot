import json
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from database import Database
from helpers import create_feedback_blocks

# Initializes your app with your bot token and socket mode handler
app = App(process_before_response=True)
db = Database()


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
    db.put_item(team)

    for member in team['members']:
        db.put_item({
            'team': team_name,
            'sk': 'user#' + member,
            'completed_feedback': False
        })
        client.chat_postMessage(
            channel=member,
            text=f"You have been added to the feedback loop for *{team_name}*. You will now receive feedback requests to"
                 f" fill out for your teammates.",
        )


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
