terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.AWS_REGION

  # Portfolio/demo mode: the pipeline only generates and audits the Terraform plan.
  # No infrastructure is deployed and no AWS authentication is required.
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation      = true

  default_tags {
    tags = {
      Project     = var.PROJECT
      Environment = var.ENVIRONMENT
      Owner       = var.OWNER
      ManagedBy   = "Terraform"
    }
  }
}
