## ecs service associated with aws service discovery service

data "aws_subnet_ids" "main" {
  vpc_id = "${var.vpc_id}"
}

# replacing this resource will require complete stop of related service
# remove service manually first, and run terraform apply again after service stops
resource "aws_service_discovery_service" "main" {
  name = "${var.service_label}"

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

  service_registries {
    registry_arn = "${aws_service_discovery_service.main.arn}"
  }
}

output "service_name" {
  value = "${aws_ecs_service.main.name}"
}
