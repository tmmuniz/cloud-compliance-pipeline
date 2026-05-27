resource "aws_instance" "app" {
  ami                         = var.MOCK_AMI_ID
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.private.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  associate_public_ip_address = false
  iam_instance_profile        = aws_iam_instance_profile.app.name
  monitoring                  = true

  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    encrypted   = true
    volume_size = 30
    volume_type = "gp3"
  }

  tags = {
    Name        = "${var.PROJECT}-app"
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}
