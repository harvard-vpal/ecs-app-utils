# ECS app utils

Utilities for deploying Django app (nginx/app, rabbitmq, celery worker) with AWS ECS Fargate.

## Contents

### Terraform modules
* `terraform/`
    * `network/` - load balancer, target group, routing, other network resources
    * `services/`
        * `load_balanced` - ECS service connected to load balancer target group (e.g. nginx/web)
        * `discoverable` - ECS service with service discovery (e.g. RabbitMQ)
        * `generic` - ECS service with no load balancer or service discovery
