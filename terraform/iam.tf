resource "aws_iam_role" "flow_logs" {
  name = "${var.PROJECT}-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_iam_policy" "flow_logs" {
  name = "${var.PROJECT}-flow-logs-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "flow_logs" {
  role       = aws_iam_role.flow_logs.name
  policy_arn = aws_iam_policy.flow_logs.arn
}

resource "aws_iam_role" "app" {
  name = "${var.PROJECT}-app-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Project     = var.PROJECT
    Environment = var.ENVIRONMENT
    Owner       = var.OWNER
  }
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.PROJECT}-app-profile"
  role = aws_iam_role.app.name
}
