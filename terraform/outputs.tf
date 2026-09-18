output "instance_id" {
  description = "EC2 instance ID of the monitored server"
  value       = aws_instance.monitored_server.id
}

output "instance_public_ip" {
  description = "Public IP address to set as EC2_HOST in ConfigSentinel's .env"
  value       = aws_instance.monitored_server.public_ip
}

output "security_group_id" {
  value = aws_security_group.configsentinel_sg.id
}

output "iam_role_name" {
  value = aws_iam_role.ec2_role.name
}
