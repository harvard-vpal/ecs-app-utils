## web ecs service

data "aws_subnet_ids" "main" {
  vpc_id = "${var.vpc_id}"
}

data "aws_iam_role" "task_execution" {
  name = "ecsTaskExecutionRole"
}

data "template_file" "container_definitions" {
  template = "${file("${path.module}/container_definitions.tpl")}"

  vars {
    web_image = "${var.web_image}"
    nginx_image = "${var.nginx_image}"
    project = "${var.project}"
    env_label = "${var.env_label}"
    log_group_name = "${var.log_group_name}"
  }
}

resource "aws_ecs_task_definition" "main" {
  family                = "${var.project}-${var.env_label}-web"
  container_definitions = "${data.template_file.container_definitions.rendered}"
  execution_role_arn = "${data.aws_iam_role.task_execution.arn}" # required for awslogs
  task_role_arn = "${var.role_arn}"
  network_mode = "awsvpc"
  memory = 512
  cpu = 256
  requires_compatibilities = ["FARGATE"]
}

resource "aws_ecs_service" "main" {
  name            = "${var.project}-${var.env_label}-web"
  cluster         = "${var.cluster_name}"
  task_definition = "${aws_ecs_task_definition.main.arn}"
  desired_count   = 1
  launch_type     = "FARGATE"

  load_balancer {
    target_group_arn = "${var.target_group_arn}"
    container_name   = "nginx"
    container_port   = 80
  }

  network_configuration {
    subnets = ["${data.aws_subnet_ids.main.ids}"],
    security_groups = ["${var.security_group_id}"]
    assign_public_ip = true
  }
}
