import os
import json
from dotenv import load_dotenv, find_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from helpers import create_feedback_blocks

load_dotenv(find_dotenv())

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get('SLACK_BOT_TOKEN'))


@app.command('/setup_feedback_loop')
@app.shortcut("setup_feedback_loop")
def setup_feedback(ack, body, client):
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
                    "type": "section",
                    "block_id": "multi_users_select_section",
                    "text": {"type": "mrkdwn", "text": "*Who is in the loop?*"},
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
                    "block_id": "time_c",
                    "label": {"type": "plain_text", "text": "How often do you want this to occur?"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "time_input"
                    }
                }
            ]
        }
    )


@app.action("setup_users")
@app.action("user")
def handle_user_select(ack):
    ack()


@app.action('open_feedback')
def open_feedback(ack, body, client):
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


@app.command("/send_feedback")
@app.shortcut("send_feedback")
def open_feedback_manual(ack, body, client):
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


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get('SLACK_APP_TOKEN')).start()
