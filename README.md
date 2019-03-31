# ECS app utils

Utilities for deploying Django app (nginx/app, rabbitmq, celery worker) with AWS ECS Fargate.

## Contents

### Terraform modules
* `terraform/`
    * `network/` - load balancer, target group, routing, other network resources
        * `base` - load balancer policy not included - useful for utilizing custom inbound traffic rules
        * `public` - load balancer policy included that allows all inbound traffic
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

### Environment variables
* `UTILS_CONTEXT`: local path to ecs_utils package

### Recommended docker-compose configuration
A docker-compose file should be created, outside of the ecs-app-utils source. Starting point:

```
version: '3'
services:
  # for running build/deploy tasks
  deploy:
    build:
      context: .
    volumes:
      # mount working directory
      - .:/home
      # enable connecting to host docker socket
      - /var/run/docker.sock:/var/run/docker.sock
      # local docker binary usually at /usr/bin/docker or /usr/local/bin/docker
      - ${DOCKER_BINARY}:/usr/bin/docker
      # mount ecs utils
      - ${UTILS_CONTEXT}:/home/utils
      # mount AWS credential info
      - ${HOME}/.aws/credentials:/root/.aws/credentials
      # mount app code to src
      - ${APP_REPO}:/home/build/app/src
      # mount settings in src for build
      - ./build/app/settings:/home/build/app/src/config/settings
    env_file:
      - .env
    environment:
      # override APP_REPO from local path to container path
      - APP_REPO=build/app/src
    entrypoint: python -m ecs_utils
```
Code examples assume that the service is named `deploy` and the `deploy` entrypoint has been set up.

### Using terraform modules
Typical outline:
* Define custom security groups and policies
* Use network module
* Define web container definition
* Use web service module
* Define other container definitions + use more service modules if applicable

Required terraform outputs to expose in order to use redeploy or fargate commands:
* `cluster_name` - used in redeploy and fargate commands
* `service_name` - used in redeploy command
* `security_group` - used in fargate command
* `subnet_ids` - used in fargate command
* `job_task_definition_family` - used in fargate command

e.g.
```
output "cluster_name" {
  value = "${var.cluster_name}"
}

output "service_name" {
  value = "${module.web_service.service_name}"
}

output "security_group" {
  value = "${aws_security_group.ecs_service.id}"
}

output "subnet_ids" {
  value = "${data.aws_subnet_ids.main.ids}"
}

output "job_task_definition_family" {
  value = "${aws_ecs_task_definition.task.family}"
}
```


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


### Dropping into bash environment (custom jobs or debugging)
```
docker-compose run --entrypoint=/bin/bash deploy
```

## Usage

### Deploy entrypoint

Example usage of `bin/deploy` command line entrypoint:

```bash
# Build images with current app code and tag images with 'latest'
deploy build

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
