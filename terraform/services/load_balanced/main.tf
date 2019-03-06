## ecs service associated with load balancer target group

data "aws_subnet_ids" "main" {
  vpc_id = "${var.vpc_id}"
}

resource "aws_ecs_task_definition" "main" {
  family                = "${var.name}"
  container_definitions = "${var.container_definitions}"
  execution_role_arn = "${var.execution_role_arn}" # required for awslogs
  task_role_arn = "${var.role_arn}"
  network_mode = "awsvpc"
  memory = "${var.memory}"
  cpu = "${var.cpu}"
  requires_compatibilities = ["FARGATE"]
}

resource "aws_ecs_service" "main" {
  name            = "${var.name}"
  cluster         = "${var.cluster_name}"
  task_definition = "${aws_ecs_task_definition.main.arn}"
  desired_count   = "${var.count}"
  launch_type     = "FARGATE"

  load_balancer {
    target_group_arn = "${var.target_group_arn}"
    container_name   = "${var.load_balancer_container_name}"
    container_port   = 80
  }

  network_configuration {
    subnets = ["${data.aws_subnet_ids.main.ids}"],
    security_groups = ["${var.security_group_id}"]
    assign_public_ip = true
  }
}

output "service_name" {
  value = "${aws_ecs_service.main.name}"
}
