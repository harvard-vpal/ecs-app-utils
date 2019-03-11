# variables for generic service module

variable "vpc_id" {
  description = "Id of VPC associated with ECS cluster, e.g. vpc-xxxxx "
}

variable "name" {
  description = "Name to use for task definition and service, e.g. engine-dev-web"
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

variable "execution_role_arn" {
  description = "ARN of ecs task execution role"
}
