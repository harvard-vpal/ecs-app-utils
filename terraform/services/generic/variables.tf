# variables for web service module

variable "vpc_id" {
  description = "Id of VPC associated with ECS cluster, e.g. vpc-xxxxx "
}

variable "env_label" {
  description = "Environment type label, e.g. dev, test, prod"
}

variable "project" {
  description = "App label, e.g. engine, bridge"
}

variable "target_group_arn" {
  description = "ARN of ALB target group to associate service with"
}

variable "role_arn" {
  description = "ARN of role to associate with task run"
}

variable "cluster_name" {
  description = "ECS cluster name"
}

variable "security_group_id" {
  description = "Security group ID to use for service"
}

variable "log_group_name" {
  description = "Cloudwatch log group name"
}

variable "web_image" {
  description = "image and tag for web image"
}

variable "nginx_image" {
  description = "image and tag for nginx image"
}

variable "container_definitions_file" {
  description = "container definitions file"
  default = "$${file("$${path.module}/container_definitions.tpl")}"
}

variable "memory" {
  description = "Task memory"
  default = 512
}

variable "cpu" {
  description = "Task cpu"
  default = 256
}

variable "count" {
  description = "Desired task count"
  default = 1
}

variable "target_group_container_name" {
  description = "Container name for load balancer target group to reference"
  default = "nginx"
}