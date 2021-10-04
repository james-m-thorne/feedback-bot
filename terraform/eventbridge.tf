
resource "aws_cloudwatch_event_rule" "reminder_rule" {
  name        = "feedback-reminder"
  description = "Feedback reminder for users who have not completed their feedback"
  schedule_expression = "cron(0 0 ? * FRI *)"
}

resource "aws_cloudwatch_event_target" "reminder_target" {
  rule = aws_cloudwatch_event_rule.reminder_rule.name
  arn  = module.reminder_lambda.lambda_function_arn
}