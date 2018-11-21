# variables for rabbit service module

variable "vpc_id" {
  description = "Id of VPC associated with ECS cluster, e.g. vpc-xxxxx"
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

variable "log_group_name" {
  description = "Cloudwatch log group name"
}

variable "security_group_id" {
  description = "Security group ID to use for service"
}

variable "service_discovery_namespace_id" {
  description = "Service discovery namespace id"
}