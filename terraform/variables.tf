variable "aws_region" {
  description = "AWS region used by the portfolio lab."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project tag value."
  type        = string
  default     = "cloud-compliance-pipeline"
}

variable "environment" {
  description = "Environment tag value."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Owner tag value."
  type        = string
  default     = "portfolio"
}

variable "allowed_ssh_cidr" {
  description = "CIDR allowed for SSH access. Avoid 0.0.0.0/0."
  type        = string
  default     = "203.0.113.10/32"
}
