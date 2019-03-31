variable "policy_arn" {
    description = "ARN of custom policy to attach to role"
}

variable "role_name" {
    description = "Name for role (e.g. project-dev-ecsTaskExecutionRole)"
}

output "arn" {
  description = "role arn"
  value = "${aws_iam_role.execution.arn}"
}