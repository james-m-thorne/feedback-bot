import boto3


class Database:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.teams_table = self.dynamodb.Tbale('feedback')

        for team in TEAMS:
            self.teams_table.put_item(Item=team)

    def get_team(self, team_name):
        return self.teams_table.get_item(Key={'name': team_name})

    def get_all_teams(self):
        return self.teams_table.scan()
