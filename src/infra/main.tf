module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 7.0"

  function_name = "shc-calculator"
  description   = "My awesome lambda function"
  handler       = "src.python.soft_sensors.handler.handle"
  runtime       = "python3.11"
  memory_size   = 512

  attach_policy = true
  policy = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"

  create_package         = false
  local_existing_package = "../../dist/src.python.soft_sensors/lambda.zip"

  layers = [
    var.wrangler_layer_arn
  ]

  tags = {
    Name = "my-lambda1"
  }
}

resource "aws_s3_bucket" "this" {
  bucket_prefix = "cre-data-shc"
  force_destroy = true
}

locals {
  files = toset([
    "plant-data/abc.csv",
    "plant-data/abc.README.md",
    "plant-data/bcd.csv",
    "plant-data/bcd.README.md",
    "plant-data/cde.csv",
    "plant-data/cde.README.md",
    "plant-data/def.csv",
    "plant-data/def.README.md",
  ])
}

resource "aws_s3_object" "data" {
  for_each = local.files
  bucket   = aws_s3_bucket.this.bucket
  key      = split("/", each.value)[1]
  source   = each.value
  etag     = filemd5(each.value)
}
