# ECS app utils

Utilities for deploying applications with AWS ECS Fargate.

## About

### Motivation
This project came out of the need to deploy multiple containerized applications in a way that:
* automates provisioning of instructure
* supports the deployment of specific versions
* supports application-specific architectures (different types of services, different network access rules)
* supports the use and independent management of multiple environments (dev, stage, prod) for each application
* has a consistent interface for performing common deployment tasks
* decouples deployment configuration from application code, allowing public application code to be separated from private deployment-specific code and settings

### ecs-app-utils framework
The ecs-app-utils framework is a way of using the utilities in this repo to configure and manage the deployment of dockerized applications.

Using this framework, applications can be deployed on AWS, running on ECS Fargate, which the ability to manage deployments via a command line interface.

Typically, a repo will be set up containing deployment configuration for the specific deployment. This is separate from the repo containing applciation code.


### Deployment commands
Applications using the ecs-app-utils framework can use CLI actions to manage deployment tasks. For example:

**Building application image based on github tag `1.0.1`**
```
bin/deploy build --tag 1.0.1
```

**Pushing application image with version 1.0.1 to image repository**
```
bin/deploy push --tag 1.0.1
```

**Deploying application version 1.0.1 to environment `dev`** 
```
bin/deploy apply --tag 1.0.1 --env dev
```

### Repo contents

This repo contains common utilities that are used when configuring deployment with the ecs-app-utils framework. There are two main components:
* `ecs-utils/`: python package implementing the CLI
* `terraform/`: Terraform modules that can be used 

#### `ecs-utils` package
CLI helper for common DevOps tasks (docker build, docker push, terraform apply, ECS service redeploy) when working with an application deployed on ECS.

#### Terraform modules
* `terraform/`
    * `network/` - load balancer, target group, routing, other network resources
        * `base` - load balancer policy not included - useful for utilizing custom inbound traffic rules
        * `public` - load balancer policy included that allows all inbound traffic
    * `services/`
        * `load_balanced` - ECS service connected to load balancer target group (e.g. nginx/web)
        * `discoverable` - ECS service with service discovery (e.g. RabbitMQ)
        * `generic` - ECS service with no load balancer or service discovery (e.g. Celery worker)
    * `execution_role` - task execution role where custom policy can be specified. Usually used to specify custom policy to allow access to SSM params if using ECS secrets in container definitions.

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



### Recommended docker-compose configuration

#### `docker-compose.yml`
It is recommended to use a docker environment to define the runtime environment for building images and running terraform. Use a `docker-compose.yml` file to:
* mount AWS credential info (for accessing AWS ECR repos and for Terraform to use when applying infrastructure)
* mount host Docker socket (build images on host)

If applicable, other configuration may include
* mount ecs-app-utils python package or terraform modules for development
* mount app code if not pulling from github for base app image build

Example `docker-compose.yml`:

```yaml
version: '3'
services:
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
      # mount AWS credential info
      - ${HOME}/.aws/credentials:/root/.aws/credentials
      # (optional depending on docker-compose.build)
      # mount app code to src
      - ${APP_REPO}:/home/build/app_base/src
      # (optional) mount ecs utils python package from local copy
      - ${ECS_UTILS_CONTEXT}/ecs_utils:/src/ecs-utils/ecs_utils
      # (optional) mount ecs utils terraform modules from local copy
      - ${ECS_UTILS_CONTEXT}/terraform:/src/terraform
    env_file:
      - .env
    entrypoint: python -m ecs_utils
```

#### `build/docker-compose.build.yml`

It is also assumed that there is a `build/docker-compose.build.yml` file specifying configurations for the images to be built.

ecs-utils passes the `--tag` argument to docker-compose build as the environment variable `APP_TAG`, which can be used to control the build image tags with "${APP_TAG}"

Example `build/docker-compose.build.yml`:
```yaml

version: '3'
services:
  # base app image
  app_base:
    image: ${APP_IMAGE}:${APP_TAG}-base
    build:
      dockerfile: Dockerfile_opt
      # context: app_base/src/bridge_adaptivity  # if building from local version; ensure volume mount is configured in other docker-compose

      # build from github, using reference APP_TAG and bridge_adaptivity subdirectory
      context: https://github.com/harvard-vpal/bridge-adaptivity.git#${APP_TAG}:bridge_adaptivity

  # copy custom settings into base app image (see Dockerfile)
  app:
    build:
      context: app
      args:
        - APP_IMAGE=${APP_IMAGE}:${APP_TAG}-base
    image: ${APP_IMAGE}:${APP_TAG}
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.custom

  # custom nginx image build that collects static assets from app image and copies to nginx image
  nginx:
    build:
      context: nginx
      args:
        - APP_IMAGE=${APP_IMAGE}:${APP_TAG}
    image: ${NGINX_IMAGE}:${APP_TAG}

```

Example `build/` directory:
```
build/
    docker-compose.build.yml
    app/
        Dockerfile
        settings.py
    nginx/
        Dockerfile
        sites-enabled/
            web.conf
```

### Environment variables for configuration

Depends on what variables were used in `docker-compose.yml`, but a typical example could be:
```
AWS_DEFAULT_REGION=us-east-1
DOCKER_BINARY=/usr/local/bin/docker

# these could also just be hard coded in docker-compose.build.yml
APP_IMAGE=361808764124.dkr.ecr.us-east-1.amazonaws.com/bridge/app
NGINX_IMAGE=361808764124.dkr.ecr.us-east-1.amazonaws.com/bridge/nginx

# optional for overriding with local versions
ECS_UTILS_CONTEXT=/Users/ama571/github/ecs-app-utils
APP_REPO=/Users/ama571/github/bridge-adaptivity
```

### Using terraform modules

Write your own `main.tf`, using some of the modules provided here.

Typical outline:
* Define custom security groups and policies
* Use a network module
* Define web container definition (with a `template_file` data resource)
* Use a web service module
* Define other container definitions + use more service modules if applicable

Required terraform outputs to expose in order to use redeploy or fargate commands:
* `cluster_name` - used in redeploy and fargate commands
* `services` - map of service labels to rendered service name; used in redeploy command
* `security_group` - used in fargate command
* `subnet_ids` - used in fargate command
* `job_task_definition_family` - used in fargate command

e.g.
```
output "cluster_name" {
  value = "${var.cluster_name}"
}

output "services" {
  description = "mapping from short service name to rendered service name"
  value = {
    "web" = "${var.project}-${var.env_label}-web"
    "rabbit" = "${var.project}-${var.env_label}-rabbit"
    "worker" = "${var.project}-${var.env_label}-worker"
  }
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

#### Create terraform workspace per environment (dev/stage/prod)

Create workspace `dev`:
```
docker-compose run app deploy create --env dev
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

# Redeploy services (force restart of services, even if no config changes)
deploy redeploy --env dev web worker
```
