# Network module to set up web routing resources for ecs service
# Load balancer security group is created outside of module, for cases that require custom network rules


data "aws_subnet_ids" "main" {
  vpc_id = "${var.vpc_id}"
}

data "aws_route53_zone" "main" {
  name         = "${var.hosted_zone}"
}

resource "aws_alb" "main" {
  name            = "${var.project}-${var.env_label}"
  subnets         = ["${data.aws_subnet_ids.main.ids}"]
  security_groups = ["${var.security_group_id}"]
}

resource "aws_alb_listener" "https" {
  load_balancer_arn = "${aws_alb.main.id}"
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "${var.ssl_certificate_arn}"

  default_action {
    type             = "fixed-response"

    fixed_response {
      content_type = "text/plain"
      message_body = "Service Temporarily Unavailable (ALB Default Action)"
      status_code  = "503"
    }
  }
}

resource "aws_alb_listener" "http" {
  load_balancer_arn = "${aws_alb.main.id}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_route53_record" "main" {
  zone_id = "${data.aws_route53_zone.main.zone_id}"
  name    = "${var.domain_name}"
  type    = "A"

  alias {
    name                   = "${aws_alb.main.dns_name}"
    zone_id                = "${aws_alb.main.zone_id}"
    evaluate_target_health = false
  }
}

## Assumes only one service is being load balanced but may make sense to move these to service modules if not the case

resource "aws_alb_target_group" "main" {
  name_prefix = "${var.short_project_label}"  # using name_prefix instead of name used because of create_before_destroy option
  port        = "${var.container_port}"
  protocol    = "HTTP"
  target_type = "ip"  # required for use of awsvpc task networking mode
  vpc_id      = "${var.vpc_id}"

  health_check {
    path = "${var.health_check_path}"
  }

  # Resolves: (Error deleting Target Group: Target group is currently in use by a listener or a rule)
  lifecycle {
    create_before_destroy = true
  }

  # Resolves: The target group does not have an associated load balancer
  depends_on = ["aws_alb.main"]
}

resource "aws_alb_listener_rule" "main" {
  listener_arn = "${aws_alb_listener.https.arn}"

  action {
    target_group_arn = "${aws_alb_target_group.main.id}"
    type             = "forward"
  }
  condition {
    field = "path-pattern"
    values = ["*"]
  }
}
