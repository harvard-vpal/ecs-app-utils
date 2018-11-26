# ECS app utils

Utilities for deploying Django app (nginx/app, rabbitmq, celery worker) with AWS ECS Fargate.

## Contents

### Terraform modules
* `terraform/`
    * `network/` - load balancer, target group, routing, other network resources
    * `services/`
        * `load_balanced` - ECS service connected to load balancer target group (e.g. nginx/web)
        * `discoverable` - ECS service with service discovery (e.g. RabbitMQ)
        * `generic` - ECS service with no load balancer or service discovery (e.g. Celery worker)

## Getting started

### AWS requirements
The Terraform config assumes a couple of AWS resources are manually created prior to setting up the rest of the resources (these can be set up via the console).
* ECS cluster (`cluster_name` is the name of the ECS cluster)
* SSL certificate (`ssl_certificate_arm` is the ARN of the certificate)
* Cloudwatch log group

## Usage

### Deploy entrypoint

Example usage of `bin/deploy` command line entrypoint:

```bash
# Build images with current app code and tag images with 'latest', (TODO --env arg is required atm but doesn't do anything here)
deploy build --env dev

# Checkout the app code with the specified version and tag image with that tag
deploy build --env dev --version 1.0.0

# Push images with the specified tag to ECR repositories
deploy push --env dev

# Run 'terraform plan' with specified image tag against 'dev' environment
deploy plan --env dev --tag 1.0.0

# Run 'terraform apply' with specified image tag against 'dev' environment
deploy apply --env dev --tag 1.0.0

# Build, push, and apply
deploy all --env dev --tag 1.0.0
```
