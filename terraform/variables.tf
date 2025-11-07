variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "report_bucket_name" {
  description = "S3 bucket name for cost optimization reports"
  type        = string
  default     = "aws-cost-optimizer-reports"
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
  default     = "aws-cost-optimizer"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "schedule_expression" {
  description = "EventBridge schedule expression"
  type        = string
  default     = "cron(0 9 * * ? *)"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
}

variable "slack_channel" {
  description = "Slack channel for notifications"
  type        = string
  default     = "#team-collab"
}

variable "idle_ec2_days" {
  description = "Days before EC2 is considered idle"
  type        = number
  default     = 7
}

variable "idle_rds_days" {
  description = "Days before RDS is considered idle"
  type        = number
  default     = 7
}

variable "auto_terminate" {
  description = "Auto-terminate idle resources"
  type        = bool
  default     = false
}

variable "cost_threshold" {
  description = "Cost threshold for alerts"
  type        = number
  default     = 50
}

