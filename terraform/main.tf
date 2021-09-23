terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket = "xero-process-support-640077214053-ap-southeast-2"
    key    = "xero-sre/terraform-state/feedback-bot/terraform.tfstate"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "ap-southeast-2"

  ignore_tags {
    key_prefixes = ["managed:"]
  }
}
