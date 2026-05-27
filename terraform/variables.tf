variable "AWS_REGION" {
  description = "AWS region used by Terraform."
  type        = string
  default     = "us-east-1"
}

variable "PROJECT" {
  description = "Project tag."
  type        = string
  default     = "cloud-compliance-pipeline"
}

variable "ENVIRONMENT" {
  description = "Environment tag."
  type        = string
  default     = "dev"
}

variable "OWNER" {
  description = "Owner tag."
  type        = string
  default     = "security-team"
}

variable "ALLOWED_PUBLIC_IP_CIDR" {
  description = "Public CIDR allowed to access administrative ports when required."
  type        = string
  default     = "203.0.113.10/32"
}

variable "MOCK_AMI_ID" {
  description = "Static AMI ID used only to build a demo Terraform plan without querying AWS."
  type        = string
  default     = "ami-0123456789abcdef0"
}
