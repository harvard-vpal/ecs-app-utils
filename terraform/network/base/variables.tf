# variables for network module

variable "vpc_id" {
  description = "Id of VPC associated with ECS cluster, e.g. vpc-xxxxx"
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate"
}

variable "hosted_zone" {
  description = "Route 53 hosted zone to create record set in"
}

variable "domain_name" {
  description = "Domain name / name to use for route53 record set"
}

variable "env_label" {
  description = "Environment type label, e.g. dev, test, prod"
}

variable "project" {
  description = "App label, e.g. engine, bridge"
}

variable "short_project_label" {
  description = "short project label that is 6 chars or fewer"
}

variable "security_group_id" {
  description = "load balancer security group id"
}

variable "container_port" {
  description = "container port for target group"
  default = 80
}

variable "health_check_path" {
  description = "health check path"
  default = "/health/"
}

output "listener_arn" {
  value = "${aws_alb_listener.https.arn}"
}

output "target_group_arn" {
  value = "${aws_alb_target_group.main.arn}"
}

output "security_group_id" {
  description = "load balancer security group id"
  value = "${var.security_group_id}"
}
