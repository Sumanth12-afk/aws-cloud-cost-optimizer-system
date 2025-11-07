# Package Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda"
  output_path = "${path.module}/lambda_function.zip"
}

# Lambda function
resource "aws_lambda_function" "cost_optimizer" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.lambda_function_name
  role            = aws_iam_role.lambda_role.arn
  handler         = "main.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory

  environment {
    variables = {
      SLACK_WEBHOOK_URL      = var.slack_webhook_url
      SLACK_CHANNEL          = var.slack_channel
      SLACK_USERNAME         = "Sumanth Nallandhigal"
      REPORT_BUCKET          = aws_s3_bucket.cost_optimizer_reports.id
      IDLE_EC2_DAYS          = var.idle_ec2_days
      IDLE_RDS_DAYS          = var.idle_rds_days
      AUTO_TERMINATE         = var.auto_terminate
      COST_THRESHOLD         = var.cost_threshold
      TAG_POLICY_FILE        = "config/policy.json"
      REQUIRED_TAGS          = "Owner,Project,Environment"
      LOG_LEVEL              = "INFO"
      ENABLE_CLOUDWATCH_LOGS = "true"
    }
  }

  tags = {
    Name        = "AWS Cost Optimizer Lambda"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  depends_on = [
    aws_cloudwatch_log_group.cost_optimizer_lambda,
    aws_iam_role_policy_attachment.lambda_policy_attach
  ]
}

