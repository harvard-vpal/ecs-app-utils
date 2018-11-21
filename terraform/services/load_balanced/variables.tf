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

variable "role_arn" {
  description = "ARN of role to associate with task run"
}

variable "cluster_name" {
  description = "ECS cluster name"
}

variable "security_group_id" {
  description = "Security group ID to use for service"
}

variable "container_definitions" {
  description = "Container definitions json document"
}

variable "memory" {
  description = "Task memory allocation"
  default = 512
}

variable "cpu" {
  description = "Task cpu allocation"
  default = 256
}

variable "count" {
  description = "Desired task count"
  default = 1
}

variable "target_group_arn" {
  description = "ARN of ALB target group to associate service with"
}