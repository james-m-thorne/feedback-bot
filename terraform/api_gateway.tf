
resource "aws_apigatewayv2_api" "api" {
  name            = "Slack Feedback Bot API"
  description     = "API to proxy to external services"
  protocol_type   = "HTTP"
}

resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "prod"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 10
    throttling_rate_limit  = 100
  }
}

resource "aws_apigatewayv2_integration" "api_integration_bot" {
  api_id           = aws_apigatewayv2_api.api.id
  integration_type = "AWS_PROXY"
  integration_method = "POST"
  integration_uri  = module.slack_lambda.lambda_function_invoke_arn
}

resource "aws_apigatewayv2_route" "api_route_bot" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "POST /slack-feedback-bot"
  target = "integrations/${aws_apigatewayv2_integration.api_integration_bot.id}"
}
