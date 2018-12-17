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

**Checklist**
* Terraform workspace
* `.tfvars` file
* Django settings with ECS ips and settings from AWS SSM param store
* AWS resources not created (but referenced) by terraform
    * Cloudwatch group
    * SSL certificate
    * ECS cluster
* If migrating existing deploy, import applicable resources to terraform (e.g. route53 record)

### AWS requirements
The Terraform config assumes a couple of AWS resources are manually created prior to setting up the rest of the resources (these can be set up via the console).
* ECS cluster (`cluster_name` is the name of the ECS cluster)
* SSL certificate (`ssl_certificate_arm` is the ARN of the certificate)
* Cloudwatch log group

### Terraform workspace initialization
#### Initialize terraform workspace per environment (dev/stage/prod)

```
docker-compose run app deploy init --env dev
```

Manual:
```
docker-compose run app bash
cd Terraform
terraform workspace new dev
```

#### Create and populate a environment-specific terraform variables (`.tfvars`) file:
Example:

```
cluster_name = "alosi"
vpc_id = "vpc-337e9154"
ssl_certificate_arn = "arn:aws:acm:us-east-1:361808764124:certificate/d6c9ff43-0a7f-4ef3-bfa6-56175c79fa0f"
hosted_zone = "vpal.io."
domain_name = "stage.engine.vpal.io"
env_label = "stage"
project = "engine"
short_project_label = "engine"
app_image = "361808764124.dkr.ecr.us-east-1.amazonaws.com/engine/app:latest"
nginx_image = "361808764124.dkr.ecr.us-east-1.amazonaws.com/engine/nginx:latest"
DJANGO_SETTINGS_MODULE = "config.settings.eb.stage"
log_group_name = "/ecs/engine/stage"

```

#### Import resources if applicable
e.g.
```
terraform import module.network.aws_route53_record.main Z4KAPRWWNC7JR_stage.engine.example.com_CNAME
```
See [terraform docs](https://www.terraform.io/docs/providers/aws/r/route53_record.html#import) for more info.

#### TODO .env file documentation

## Usage

### Deploy entrypoint

Example usage of `bin/deploy` command line entrypoint:

```bash
# Build images with current app code and tag images with 'latest', (TODO --env arg is required atm but doesn't do anything here)
deploy build --env dev

# Checkout the app code with the specified version and tag image with that tag
deploy build --tag 1.0.0

# Push images with the specified tag to ECR repositories
deploy push --tag 1.0.0

# Run 'terraform plan' with specified image tag against 'dev' environment
deploy plan --tag 1.0.0 --env dev

# Run 'terraform apply' with specified image tag against 'dev' environment
deploy apply --tag 1.0.0 --env dev

# Build, push, and apply
deploy all --tag 1.0.0 --env dev
```
