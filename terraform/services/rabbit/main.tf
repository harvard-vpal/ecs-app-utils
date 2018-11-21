## rabbit ecs service

data "aws_subnet_ids" "main" {
  vpc_id = "${var.vpc_id}"
}

data "aws_iam_role" "task_execution" {
  name = "ecsTaskExecutionRole"
}

# replacing this resource will require complete stop of related service
# remove service manually first, and run terraform apply again after service stops
resource "aws_service_discovery_service" "main" {
  name = "rabbit"

  dns_config {
//    namespace_id = "${aws_service_discovery_private_dns_namespace.main.id}"
    namespace_id = "${var.service_discovery_namespace_id}"

    dns_records {
      ttl = 10
      type = "A"
    }
  }

  # Resolves: ECS task being stuck in "activating" status
  # https://forums.aws.amazon.com/thread.jspa?threadID=283572
  health_check_custom_config {
      failure_threshold = 1
  }
}

data "template_file" "container_definitions" {
  template = "${file("${path.module}/container_definitions.tpl")}"

  vars {
    project = "${var.project}"
    env_label = "${var.env_label}"
    log_group_name = "${var.log_group_name}"
  }
}


resource "aws_ecs_task_definition" "main" {
  family                = "${var.project}-${var.env_label}-rabbit"
  container_definitions = "${data.template_file.container_definitions.rendered}"
  execution_role_arn = "${data.aws_iam_role.task_execution.arn}" # required for awslogs
  task_role_arn = "${var.role_arn}"
  network_mode = "awsvpc"
  memory = 512
  cpu = 256
  requires_compatibilities = ["FARGATE"]
}


resource "aws_ecs_service" "main" {
  name            = "${var.project}-${var.env_label}-rabbit"
  cluster         = "${var.cluster_name}"
  task_definition = "${aws_ecs_task_definition.main.arn}"
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets = ["${data.aws_subnet_ids.main.ids}"],
    security_groups = ["${var.security_group_id}"]
    assign_public_ip = true
  }

  service_registries {
    registry_arn = "${aws_service_discovery_service.main.arn}"
  }
}
