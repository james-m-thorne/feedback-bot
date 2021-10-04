import os
import boto3
from slack_sdk import WebClient


def lambda_handler(event, _):
    print(f'Starting to send feedback reminders for {event}')
    slack_client = WebClient(token=os.environ.get('SLACK_BOT_TOKEN'))
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('feedback')

    get_response = table.scan(
        FilterExpression="begins_with(#sk, :user) AND #completed_feedback = :completed_feedback",
        ExpressionAttributeNames={"#sk": 'sk', "#completed_feedback": "completed_feedback"},
        ExpressionAttributeValues={":user": 'user', ":completed_feedback": False}
    )
    users = get_response['Items']

    print(f'Sending reminders for users {users}')
    for user in users:
        user_id = user['sk'].replace('user#', '')
        slack_client.chat_postEphemeral(
            channel=user_id,
            user=user_id,
            text="Friendly reminder to complete your feedback",
        )

    return {
        "statusCode": 200,
        "body": f"Successfully sent feedback reminders for {users}"
    }
