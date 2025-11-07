output "lambda_function_arn" {
  description = "ARN of the cost optimizer Lambda function"
  value       = aws_lambda_function.cost_optimizer.arn
}

output "lambda_function_name" {
  description = "Name of the cost optimizer Lambda function"
  value       = aws_lambda_function.cost_optimizer.function_name
}

output "s3_bucket_name" {
  description = "S3 bucket for cost reports"
  value       = aws_s3_bucket.cost_optimizer_reports.id
}

output "s3_bucket_arn" {
  description = "ARN of S3 bucket for cost reports"
  value       = aws_s3_bucket.cost_optimizer_reports.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for Lambda"
  value       = aws_cloudwatch_log_group.cost_optimizer_lambda.name
}

output "eventbridge_rule_arn" {
  description = "ARN of EventBridge rule"
  value       = aws_cloudwatch_event_rule.daily_trigger.arn
}

output "iam_role_arn" {
  description = "ARN of Lambda IAM role"
  value       = aws_iam_role.lambda_role.arn
}

