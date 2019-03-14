# Network module to set up web routing resources for ecs service
# Provides a default security group suitable for public web services, and uses base network module


resource "aws_security_group" "load_balancer" {
  description = "controls access to the application load balancer"

  vpc_id = "${var.vpc_id}"
  name_prefix   = "alb"

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = ["0.0.0.0/0"]
  }
}

# web routing; load balancer, target group, listener, dns records, security groups
module "network" {
  source = "../base"

  vpc_id = "${var.vpc_id}"
  ssl_certificate_arn = "${var.ssl_certificate_arn}"
  hosted_zone = "${var.hosted_zone}"
  domain_name = "${var.domain_name}"
  env_label = "${var.env_label}"
  project = "${var.project}"
  short_project_label = "${var.short_project_label}"
  security_group_id = "${aws_security_group.load_balancer.id}"
  container_port = "${var.container_port}"
  health_check_path = "${var.health_check_path}"
}
