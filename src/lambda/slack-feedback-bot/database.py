import boto3


class Database:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
        self.teams_table = self.dynamodb.Table('feedback')

    def get_team(self, team_name):
        return self.teams_table.get_item(Key={'team': team_name, 'sk': 'team'})

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
