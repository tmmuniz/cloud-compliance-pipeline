resource "aws_kms_key" "main" {
  description             = "KMS key for compliance lab encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_s3_bucket" "data" {
  bucket_prefix = "${var.PROJECT}-data-"

  tags = {
    Name        = "${var.PROJECT}-data"
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
    DataClass   = "Confidential"
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.main.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_logging" "data" {
  bucket = aws_s3_bucket.data.id
  target_bucket = aws_s3_bucket.data.id
  target_prefix = "access-logs/"
}
