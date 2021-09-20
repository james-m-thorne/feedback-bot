
resource "aws_dynamodb_table" "feedback" {
  name             = "feedback"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "team"
  range_key        = "sk"
  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  attribute {
    name = "team"
    type = "S"
  }

  attribute {
    name = "sk"
    type = "S"
  }

  tags = {
    Name        = "test"
    Environment = "production"
  }
}