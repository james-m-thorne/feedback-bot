import boto3


class Database:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.teams_table = self.dynamodb.Table('feedback')

    def get_team(self, team_name):
        return self.teams_table.get_item(Key={'name': team_name, 'sk': 'team'})

    def put_item(self, item):
        return self.teams_table.put_item(Item=item)

    def get_all(self):
        return self.teams_table.scan()
