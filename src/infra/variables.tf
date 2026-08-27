variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

# Normally you'd retrieve account ID, etc. from the environment
variable "lambda_name" {
  type    = string
  default = "soft-sensor-hello-world"
}

variable "lambda_handler" {
  type    = string
  default = "lambda_function.lambda_handler"
}

variable "lambda_runtime" {
  type    = string
  default = "python3.11"
}

variable "lambda_role_arn" {
  type        = string
  description = "The ARN of an IAM role for the Lambda to assume."
  # Example only; you could also create a role in the same code if you prefer.
  default = ""
}


variable "wrangler_layer_arn" {
  type    = string
  default = "arn:aws:lambda:eu-west-1:336392948345:layer:AWSSDKPandas-Python311:20"
}
