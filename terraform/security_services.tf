resource "aws_kms_key" "main" {
  description             = "Portfolio KMS key evaluated by compliance pipeline"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags                    = local.common_tags
}

resource "aws_cloudtrail" "main" {
  name                          = "${var.project}-trail"
  s3_bucket_name                = aws_s3_bucket.audit_logs.id
  include_global_service_events = true
  is_multi_region_trail         = true
  enable_logging                = true

  depends_on = [aws_s3_bucket_policy.audit_logs]
  tags       = local.common_tags
}

resource "aws_s3_bucket" "audit_logs" {
  bucket_prefix = "cloud-compliance-audit-logs-"
  tags          = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "cloudtrail_bucket" {
  statement {
    sid = "AWSCloudTrailAclCheck"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:GetBucketAcl"]
    resources = [aws_s3_bucket.audit_logs.arn]
  }

  statement {
    sid = "AWSCloudTrailWrite"
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.audit_logs.arn}/AWSLogs/*"]

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }
}

resource "aws_s3_bucket_policy" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id
  policy = data.aws_iam_policy_document.cloudtrail_bucket.json
}

resource "aws_guardduty_detector" "main" {
  enable = true
  tags   = local.common_tags
}

resource "aws_flow_log" "default_vpc" {
  log_destination_type = "s3"
  log_destination      = aws_s3_bucket.audit_logs.arn
  traffic_type         = "ALL"
  vpc_id               = data.aws_vpc.default.id
  tags                 = local.common_tags
}

resource "aws_backup_vault" "main" {
  name = "${var.project}-backup-vault"
  tags = local.common_tags
}

resource "aws_backup_plan" "main" {
  name = "${var.project}-backup-plan"

  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 5 ? * * *)"
  }

  tags = local.common_tags
}
