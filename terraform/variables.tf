
variable "slack_bot_token" {
  description = "Value of the slack bot token"
  type        = string
  sensitive   = true
}

variable "slack_signing_secret" {
  description = "Value of the slack signing secret"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags for AWS resources"
  type        = map(string)

  default = {
    uuid                   = "YefG92WTQ1m1hnBuKdFWkg"
  }
}
