terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 bucket for cost optimization reports
resource "aws_s3_bucket" "cost_optimizer_reports" {
  bucket = var.report_bucket_name
  tags = {
    Name        = "AWS Cost Optimizer Reports"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket_versioning" "cost_optimizer_reports" {
  bucket = aws_s3_bucket.cost_optimizer_reports.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cost_optimizer_reports" {
  bucket = aws_s3_bucket.cost_optimizer_reports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "cost_optimizer_lambda" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days
  tags = {
    Name        = "Cost Optimizer Lambda Logs"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# EventBridge rule to trigger Lambda daily
resource "aws_cloudwatch_event_rule" "daily_trigger" {
  name                = "cost-optimizer-daily-trigger"
  description         = "Trigger cost optimizer Lambda daily"
  schedule_expression = var.schedule_expression
  tags = {
    Name        = "Cost Optimizer Daily Trigger"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_trigger.name
  target_id = "CostOptimizerLambda"
  arn       = aws_lambda_function.cost_optimizer.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_optimizer.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_trigger.arn
}

