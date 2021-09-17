
resource "aws_dynamodb_table" "feedback" {
  name             = "feedback"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "name"
  stream_enabled   = true
  stream_view_type = "NEW_IMAGE"

  attribute {
    name = "name"
    type = "S"
  }

  tags = {
    Name        = "test"
    Environment = "production"
  }
}