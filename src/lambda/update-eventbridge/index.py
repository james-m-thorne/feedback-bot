import json
import boto3


def lambda_handler(event, _):
    print(f'Starting function with events: {event}')

    lambdaclient = boto3.client('lambda')
    eventclient = boto3.client('events')

    target_lambda = lambdaclient.get_function(
        FunctionName='send-feedback-requests'
    )
    target_lambda_arn = target_lambda['Configuration']['FunctionArn']

    teams = []
    for record in event['Records']:
        if record['dynamodb']['Keys']['sk']['S'] != 'team':
            continue

        team_name = record['dynamodb']['Keys']['team']['S']
        rule_name = f'feedback-rule-{team_name}'
        target_id = f'feedback-target-{team_name}'

        try:
            if record['eventName'] != 'REMOVE':
                frequency = record['dynamodb']['NewImage']['frequency']['S']
                print(f'Creating eventbridge rule with name: {rule_name}, frequency: {frequency}')
                rule_response = eventclient.put_rule(
                    Name=rule_name,
                    ScheduleExpression=f'cron({frequency})',
                    State='ENABLED',
                    Description='Team feedback frequency'
                )
                eventclient.put_targets(
                    Rule=rule_name,
                    Targets=[
                        {
                            'Id': target_id,
                            'Arn': target_lambda_arn,
                            'Input': json.dumps(record['dynamodb']['Keys'])
                        }
                    ]
                )
                try:
                    lambdaclient.add_permission(
                        FunctionName=target_lambda_arn,
                        StatementId=team_name,
                        Action='lambda:InvokeFunction',
                        Principal='events.amazonaws.com',
                        SourceArn=rule_response['RuleArn']
                    )
                except lambdaclient.exceptions.ResourceConflictException:
                    print('Skipping as permission already exists')
            else:
                print(f'Deleting eventbridge rule with name: {rule_name}')
                lambdaclient.remove_permission(
                    FunctionName=target_lambda_arn,
                    StatementId=team_name
                )
                eventclient.remove_targets(
                    Rule=rule_name,
                    Ids=[target_id]
                )
                eventclient.delete_rule(
                    Name=rule_name
                )
        except Exception as e:
            print(e)

        teams.append(team_name)

    return {
        "statusCode": 200,
        "body": f"Successfully updated rules for teams {teams}"
    }
