resource "aws_vpc" "main" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.PROJECT}-vpc"
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.20.1.0/24"
  map_public_ip_on_launch = false

  tags = {
    Name        = "${var.PROJECT}-private-subnet"
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_security_group" "app" {
  name        = "${var.PROJECT}-sg"
  description = "Application security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from approved source"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.ALLOWED_PUBLIC_IP_CIDR]
  }

  egress {
    description = "Outbound HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.PROJECT}-sg"
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_flow_log" "vpc" {
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name        = "${var.PROJECT}-vpc-flow-logs"
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}
