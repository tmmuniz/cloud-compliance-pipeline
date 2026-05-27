data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "app" {
  name        = "${var.project}-sg"
  description = "Portfolio security group evaluated by OPA"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH restricted to a specific CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "HTTP public for demo workload"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}
