
module "feedback_lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "send-feedback-requests"
  description   = "Send slack feedback requests for bot"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"
  publish       = true

  source_path = [
    {
      path = "../src/lambda/send-feedback-requests",
      pip_requirements = true
    }
  ]

  attach_policy_json = true
  policy_json = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1631835181523",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.feedback.arn}"
    }
  ]
}
  POLICY

  environment_variables = {
    SLACK_BOT_TOKEN = var.slack_bot_token
  }

  tags = var.tags
}

module "reminder_lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "send-feedback-reminders"
  description   = "Send slack feedback reminder"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"
  publish       = true

  source_path = [
    {
      path = "../src/lambda/send-feedback-reminders",
      pip_requirements = true
    }
  ]

  allowed_triggers = {
    ReminderRule = {
      principal  = "events.amazonaws.com"
      source_arn = aws_cloudwatch_event_rule.reminder_rule.arn
    }
  }

  attach_policy_json = true
  policy_json = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1631835181523",
      "Action": [
        "dynamodb:Scan"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.feedback.arn}"
    }
  ]
}
  POLICY

  environment_variables = {
    SLACK_BOT_TOKEN = var.slack_bot_token
  }

  tags = var.tags
}

module "cron_lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "update-eventbridge"
  description   = "Update eventbridge with new cron frequency"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"
  publish       = true

  source_path = "../src/lambda/update-eventbridge"

  event_source_mapping = {
    dynamodb = {
      event_source_arn           = aws_dynamodb_table.feedback.stream_arn
      starting_position          = "LATEST"
    }
  }

  allowed_triggers = {
    dynamodb = {
      principal = "dynamodb.amazonaws.com"
      source_arn = aws_dynamodb_table.feedback.stream_arn
    }
  }

  attach_policy_json     = true
  policy_json            = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1631834059137",
      "Action": [
        "lambda:GetFunction",
        "lambda:AddPermission",
        "lambda:RemovePermission"
      ],
      "Effect": "Allow",
      "Resource": "${module.feedback_lambda.lambda_function_arn}"
    },
    {
      "Sid": "Stmt1631834130307",
      "Action": [
        "events:PutRule",
        "events:PutTargets",
        "events:DeleteRule",
        "events:RemoveTargets"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Sid": "Stmt1631835181523",
      "Action": [
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator",
        "dynamodb:DescribeStream",
        "dynamodb:ListShards",
        "dynamodb:ListStreams"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.feedback.stream_arn}"
    }
  ]
}
  POLICY

  tags = var.tags
}

module "slack_lambda" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "slack-feedback-bot"
  description   = "Slack feedback bot handler"
  handler       = "index.lambda_handler"
  runtime       = "python3.8"
  publish       = true

  source_path = [
    {
      path = "../src/lambda/slack-feedback-bot",
      pip_requirements = true
    }
  ]

  allowed_triggers = {
    APIGateway = {
      principal    = "apigateway.amazonaws.com"
      source_arn = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_apigatewayv2_api.api.id}/prod/POST/slack-feedback-bot"
    }
  }

  attach_policy_json     = true
  policy_json            = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1631835181523",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:DeleteItem",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.feedback.arn}"
    }
  ]
}
  POLICY

  environment_variables = {
    SLACK_BOT_TOKEN = var.slack_bot_token
    SLACK_SIGNING_SECRET = var.slack_signing_secret
  }

  tags = var.tags
}