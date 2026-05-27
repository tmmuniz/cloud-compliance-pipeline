resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/${var.PROJECT}/flow-logs"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.main.arn

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_cloudtrail" "main" {
  name                          = "${var.PROJECT}-trail"
  s3_bucket_name                = aws_s3_bucket.data.bucket
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.main.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true
  }

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_guardduty_detector" "main" {
  enable = true

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_backup_vault" "main" {
  name        = "${var.PROJECT}-backup-vault"
  kms_key_arn = aws_kms_key.main.arn

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_backup_plan" "main" {
  name = "${var.PROJECT}-backup-plan"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 5 ? * * *)"
  }

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}
