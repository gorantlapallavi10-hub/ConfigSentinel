variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "instance_type" {
  description = "EC2 instance type for the monitored server"
  type        = string
  default     = "t2.micro" # free-tier eligible
}

variable "key_name" {
  description = "Name of an existing EC2 key pair used for SSH access"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into the instance (restrict this to your IP in production!)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "project_name" {
  description = "Name prefix used for tagging all resources"
  type        = string
  default     = "configsentinel"
}
