terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration is intentionally partial.
  # GitHub Actions injects the bucket name at runtime through TERRAFORM_STATE_BUCKET.
  backend "s3" {}
}

provider "aws" {
  region = var.AWS_REGION

  default_tags {
    tags = {
      Project     = var.PROJECT
      Environment = var.ENVIRONMENT
      Owner       = var.OWNER
      ManagedBy   = "Terraform"
    }
  }
}
