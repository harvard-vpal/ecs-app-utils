# ECS app utils

Utilities for deploying Django app (nginx/app, rabbitmq, celery worker) with AWS ECS Fargate.

## Contents

### Terraform modules
* `terraform/`
    * `network/` - load balancer, routing, other network resources
    * `services/`
        * `web` - nginx/web ECS service
        * `rabbit` - RabbitMQ ECS service
        * `worker` - celery worker ECS service
