## worker ecs service

data "aws_subnet_ids" "main" {
  vpc_id = "${var.vpc_id}"
}

data "template_file" "container_definitions" {
  template = "${file("${path.module}/container_definitions.tpl")}"

  vars {
    image = "${var.image}"
    project = "${var.project}"
    env_label = "${var.env_label}"
    log_group_name = "${var.log_group_name}"
  }
}

resource "aws_ecs_task_definition" "main" {
  family                = "${var.project}-${var.env_label}-worker"
  container_definitions = "${data.template_file.container_definitions.rendered}"
  execution_role_arn = "arn:aws:iam::361808764124:role/ecsTaskExecutionRole" # required for awslogs
  task_role_arn = "${var.role_arn}"
  network_mode = "awsvpc"
  memory = 512
  cpu = 256
  requires_compatibilities = ["FARGATE"]
}

resource "aws_ecs_service" "worker" {
  name            = "${var.project}-${var.env_label}-worker"
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
