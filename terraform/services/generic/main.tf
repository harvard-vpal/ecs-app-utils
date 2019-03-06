## rabbit ecs service

data "aws_subnet_ids" "main" {
  vpc_id = "${var.vpc_id}"
}

data "aws_iam_role" "task_execution" {
  name = "ecsTaskExecutionRole"
}

resource "aws_ecs_task_definition" "main" {
  family                = "${var.name}"
  container_definitions = "${var.container_definitions}"
  execution_role_arn = "${var.execution_role_arn}" # required for awslogs
  task_role_arn = "${var.role_arn}"
  network_mode = "awsvpc"
  memory = 512
  cpu = 256
  requires_compatibilities = ["FARGATE"]
}

resource "aws_ecs_service" "main" {
  name            = "${var.name}"
  cluster         = "${var.cluster_name}"
  task_definition = "${aws_ecs_task_definition.main.arn}"
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = ["${data.aws_subnet_ids.main.ids}"],
    security_groups = ["${var.security_group_id}"]
    assign_public_ip = true
  }
}

output "service_name" {
  value = "${aws_ecs_service.main.name}"
}
