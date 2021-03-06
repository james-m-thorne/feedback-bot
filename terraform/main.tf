terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket  = "james-thorne-terraform"
    key     = "feedback-bot/terraform.tfstate"
    region  = "us-east-1"
    profile = "personal"
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "ap-southeast-2"

  ignore_tags {
    key_prefixes = ["managed:"]
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
