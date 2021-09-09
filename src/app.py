import os
from dotenv import load_dotenv, find_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv(find_dotenv())

# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get('SLACK_BOT_TOKEN'))


@app.command('/feedbackloop')
def repeat_text(ack, respond, command):
    # Acknowledge command request
    ack()
    respond(f"{command['text']}")


# Listen for a shortcut invocation
@app.command("/sendfeedback")
@app.shortcut("send_feedback")
def open_modal(ack, body, client):
    # Acknowledge the command request
    ack()
    # Call views_open with the built-in client
    client.views_open(
        # Pass a valid trigger_id within 3 seconds of receiving it
        trigger_id=body["trigger_id"],
        # View payload
        view={
            "type": "modal",
            # View identifier
            "callback_id": "feedback_view",
            "title": {"type": "plain_text", "text": "Feedback Form"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "Send feedback to James"},
                },
                {
                    "type": "input",
                    "block_id": "input_c",
                    "label": {"type": "plain_text", "text": "What is one thing I could improve on?"},
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
def handle_submission(ack, body, client, view):
    ack()
    user = body["user"]["id"]
    text = view["state"]["values"]["input_c"]["feedback_input"]["value"]
    client.chat_postMessage(channel=user, text=text)


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get('SLACK_APP_TOKEN')).start()
