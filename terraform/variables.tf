
variable "slack_token" {
  description = "Value of the slack bot token"
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
