## custom ecs execution role that can access ssm params for ECS secrets
# specify extra policy to attach

# reference aws managed ecsTaskExecutionRole base policy
data "aws_iam_policy" "AmazonECSTaskExecutionRolePolicy" {
  arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ecs task execution role (usually ecsTaskExecutionRole)
resource "aws_iam_role" "execution" {
  name = "${var.role_name}"
  assume_role_policy= "${file("assume_role_policy.json")}"
}

resource "aws_iam_role_policy_attachment" "AmazonECSTaskExecutionRolePolicy" {
  role = "${aws_iam_role.execution.name}"
  policy_arn = "${data.aws_iam_policy.AmazonECSTaskExecutionRolePolicy.arn}"
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role = "${aws_iam_role.execution.name}"
  policy_arn = "${var.policy_arn}"
}

