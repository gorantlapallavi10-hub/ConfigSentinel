# ConfigSentinel - Terraform Infrastructure
# ----------------------------------------------
# Provisions the monitored EC2 instance, its security group, an IAM role
# with least-privilege CloudWatch read permissions, and a basic CloudWatch
# CPU alarm.
#
# NOTE: No AWS credentials are hardcoded anywhere in this file. Terraform
# picks up credentials from your environment (`aws configure`), an IAM
# role, or CI/CD secrets - exactly like boto3 does in the backend.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# --- Latest Amazon Linux 2 AMI (kept up to date automatically) ---
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# --- Security Group: only what ConfigSentinel needs to scan/manage ---
resource "aws_security_group" "configsentinel_sg" {
  name        = "${var.project_name}-sg"
  description = "Allow SSH (scanning/remediation) and HTTP (nginx) only"

  ingress {
    description = "SSH for ConfigSentinel scanning & Ansible remediation"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "HTTP - the monitored nginx web server"
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

  tags = { Name = "${var.project_name}-sg" }
}

# --- IAM Role: least-privilege, lets the instance push CloudWatch metrics ---
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "cloudwatch_agent_policy" {
  name = "${var.project_name}-cloudwatch-policy"
  role = aws_iam_role.ec2_role.id

  # Least privilege: only what the CloudWatch Agent needs to publish
  # custom metrics (e.g. memory usage) - nothing else.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cloudwatch:PutMetricData",
        "ec2:DescribeTags"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.ec2_role.name
}

# --- The monitored EC2 instance ---
resource "aws_instance" "monitored_server" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.configsentinel_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  # Installs nginx + the CloudWatch agent on first boot, matching the
  # desired_state.yaml baseline so a fresh instance starts compliant.
  user_data = <<-EOF2
    #!/bin/bash
    yum update -y
    amazon-linux-extras install nginx1 -y
    systemctl enable nginx
    systemctl start nginx
    yum install -y amazon-cloudwatch-agent
  EOF2

  tags = { Name = "${var.project_name}-monitored-instance" }
}

# --- CloudWatch alarm: notify on sustained high CPU ---
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.project_name}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Triggers when the monitored instance's CPU exceeds 80% for 10 minutes"

  dimensions = {
    InstanceId = aws_instance.monitored_server.id
  }
}
