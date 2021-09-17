import os
import json
import random
import boto3
from slack_sdk import WebClient


QUESTIONS = [
    "What is one thing I have done well?",
    "What is one thing I could improve on?",
    "How was my communication over the past week?",
    "How well do you think I have collaborated with the team?",
    "What do you think I should work on to improve myself or the work I do in the team?",
    "What is one thing I can do to be more effective in my role?"
]


def lambda_handler(event, _):
    print(f'Starting team feedback with event {event}')
    team_name = event['name']['S']

    slack_client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('feedback')

    get_response = table.get_item(Key={'name': team_name})
    team = get_response['Item']
    print(f'Sending messages for team {team}')

    members = team['members']
    feedback_count = int(team['feedback_count'])
    offset = feedback_count % (len(members) - 1)
    feedback_members = members[(offset + 1):] + members[:(offset + 1)]
    for i in range(len(members)):
        slack_client.chat_postMessage(
            channel=feedback_members[i],
            text=f"Feedback request from <@{members[i]}>",
            blocks=[
                {
                    "type": "section", "text": {"type": "mrkdwn", "text": f"Feedback request from <@{members[i]}>"}
                },
                {
                    "type": "actions",
                    "block_id": "feedback_request_button",
                    "elements": [
                        {
                            "type": "button",
                            "action_id": "open_feedback",
                            "text": {
                                "type": "plain_text",
                                "text": "Open feedback form"
                            },
                            "style": "primary",
                            "value": json.dumps(
                                {
                                    'name': team['name'], 'from_user_id': members[i],
                                    'question':random.choice(QUESTIONS), 'master_channels': team['master_channels']
                                }
                            )
                        }
                    ]
                }
            ]
        )

    table.update_item(
        Key={'name': team_name},
        ExpressionAttributeValues={':value': feedback_count + 1},
        UpdateExpression=f'SET feedback_count = :value'
    )

    return {
        "statusCode": 200,
        "body": f"Successfully sent feedback requests for {team}"
    }
