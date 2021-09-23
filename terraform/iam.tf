
resource "aws_iam_role" "feedback-role" {
  name   = "feedback-bot-role"
  assume_role_policy  = file("trustPolicy.json")
  tags = {
    "managed:ownership:team" = "sre-cobra-kai"
  }
  inline_policy {
    name    = "feedback-bot-inline-policy"
    policy  = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Stmt1631835181523",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Scan"
      ],
      "Effect": "Allow",
      "Resource": "${aws_dynamodb_table.feedback.arn}"
    }
  ]
}
  POLICY
  }
}
