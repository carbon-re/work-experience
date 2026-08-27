provider "aws" {
  region = var.aws_region
}

terraform {
  required_version = "~> 1.11.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "tfstate-backend-345594584316"
    key            = "interview"
    dynamodb_table = "tfstate-lock-345594584316"
    region         = "eu-west-2"
  }

}
