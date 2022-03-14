import boto3
from boto3.dynamodb.conditions import Key


class Database:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
        self.teams_table = self.dynamodb.Table('feedback')

    def get_team(self, team_name):
        return self.teams_table.get_item(Key={'team': team_name, 'sk': 'team'})

    def get_updated_team_members(self, team):
        current_team = self.get_team(team['team'])
        current_members = set(current_team['Item']['members'])
        new_members = team['members']
        members = []
        for member in new_members:
            if member not in current_members:
                members.append({'id': member, 'type': 'new'})
            else:
                members.append({'id': member, 'type': 'existing'})
                current_members.remove(member)
        for deleted_member in current_members:
            members.append({'id': deleted_member, 'type': 'deleted'})
        return members

    def put_item(self, item):
        return self.teams_table.put_item(Item=item)

    def delete_item(self, key):
        return self.teams_table.delete_item(Key=key)

    def get_all_teams(self):
        return self.teams_table.scan(
            FilterExpression="#sk = :team",
            ExpressionAttributeNames={"#sk": 'sk'},
            ExpressionAttributeValues={":team": 'team'}
        )
