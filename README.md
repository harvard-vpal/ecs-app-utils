# ECS app utils

Utilities for deploying applications with AWS ECS Fargate.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [About](#about)
  - [Motivation](#motivation)
  - [ecs-app-utils framework](#ecs-app-utils-framework)
  - [Functionality](#functionality)
  - [Repo contents](#repo-contents)
    - [`ecs-utils` package](#ecs-utils-package)
    - [Terraform modules](#terraform-modules)
- [Pre-setup](#pre-setup)
  - [AWS requirements](#aws-requirements)
  - [Secrets](#secrets)
  - [Application considerations](#application-considerations)
- [Setting up deploy configuration for an application](#setting-up-deploy-configuration-for-an-application)
  - [Overview](#overview)
    - [Example configuration structure](#example-configuration-structure)
    - [Variations on configuration structure](#variations-on-configuration-structure)
      - [Combined application code and deploy config](#combined-application-code-and-deploy-config)
  - [Configuring the CLI environment](#configuring-the-cli-environment)
    - [`Dockerfile`](#dockerfile)
    - [`docker-compose.yml`](#docker-composeyml)
  - [Configuring application image builds](#configuring-application-image-builds)
    - [`build/docker-compose.build.yml`](#builddocker-composebuildyml)
      - [`${APP_TAG}`](#app_tag)
      - [Image repository](#image-repository)
    - [Examples](#examples)
      - [Example 1: web app](#example-1-web-app)
      - [Examples for using local overrides](#examples-for-using-local-overrides)
  - [Configuring infrastructure with Terraform](#configuring-infrastructure-with-terraform)
    - [Terraform modules](#terraform-modules-1)
      - [Network modules](#network-modules)
      - [Service modules](#service-modules)
        - [Load Balanced](#load-balanced)
        - [Discoverable](#discoverable)
        - [Generic](#generic)
      - [Execution role](#execution-role)
    - [Required Terraform outputs](#required-terraform-outputs)
    - [Create and populate a environment-specific terraform variables (`.tfvars`) file:](#create-and-populate-a-environment-specific-terraform-variables-tfvars-file)
  - [CLI entrypoint](#cli-entrypoint)
- [Usage](#usage)
  - [Available CLI commands](#available-cli-commands)
  - [First-time setup](#first-time-setup)
    - [Create and initialize terraform workspaces](#create-and-initialize-terraform-workspaces)
    - [Running initial Terraform apply](#running-initial-terraform-apply)
  - [Typical workflow](#typical-workflow)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->



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

Using this framework, applications are deployed on AWS using ECS Fargate, with the ability to manage deployments via a command line interface.

Usage of the ecs-app-utils framework for a particular application requires writing Docker and [Terraform](https://www.terraform.io/intro/index.html) configuration to handle application-specific build and infrastructure definitions. The configuration can be located with the application code in the same repo, or separately. (Typically the configuration will be private, so having configuration separated makes sense for a public/open-source application, but may be convenient to store together if the application is also private.)


### Functionality
The ecs-app-utils framework enables the use of CLI actions to manage common deployment tasks.

Some examples:

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
* `ecs-utils/`: The python package implementing the command line interface
* `terraform/`: Terraform modules that can be referenced in application-specific Terraform configuration

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

## Pre-setup

### AWS requirements
The Terraform config assumes a couple of AWS resources are manually created prior to setting up the rest of the resources (these can be set up via the console).
* ECS cluster (`cluster_name` is the name of the ECS cluster)
* SSL certificate (`ssl_certificate_arm` is the ARN of the certificate)
* Cloudwatch log group
* ECR repository for all images being built

### Secrets
AWS SSM Param Store is useful as a secrets store, especially since [ECS provides support for using SSM Param Store parameters as secrets in ECS container definitions](https://aws.amazon.com/blogs/compute/managing-secrets-for-amazon-ecs-applications-using-parameter-store-and-iam-roles-for-tasks).

You can store sensitive configuration variables as AWS SSM Param Store parameters, and examples are provided for using SSM Param Store secrets with the ecs-app-utils framework. 

### Application considerations

The application may need internal adjustments to be able to run on AWS and/or ECS. One common consideration for Django applications is to ensure that internal IPs are added to `ALLOWED_HOSTS`, to support health checks from a load balancer. See [this gist](https://gist.github.com/kunanit/ce89d98fa654214cd0af19f12c5bd865) for an example of modifying Django settings for this context.

## Setting up deploy configuration for an application

### Overview
* Terraform workspace
* `.tfvars` file
* Django settings with ECS ips and settings from AWS SSM param store
* AWS resources not created (but referenced) by terraform
    * Cloudwatch group
    * SSL certificate
    * ECS cluster
* If migrating existing deploy, import applicable resources to terraform (e.g. route53 record)

#### Example configuration structure
In this example, `application-deploy/` is the repo folder.

```
application-deploy/
    Dockerfile
    docker-compose.yml
    terraform/
        main.tf
        container_definitions.tpl
        iam_policy.json
    build/
        docker-compose.build.yml
    bin/
      deploy

```

#### Variations on configuration structure
##### Combined application code and deploy config
In cases where the deploy config is located in a subfolder of the application code repo, it may make sense for `bin/deploy` to be outside of the configuration subfolder and instead located in the root of the repo for convenience (so that using the deploy CLI does not require changing the working directory to the configuration subfolder). In this case, `bin/deploy` should be modified from the given example to point to the correct location for the deploy `docker-compose.yml`.

### Configuring the CLI environment

The ecs-app-utils framework assumes the use of Docker to define the runtime environment for deploy tasks (i.e. building images and running terraform). This helps with reproducibility and ease of setup for others. This includes building and pushing application Docker images. This is is made possible by mounting the host Docker socket. It is important to keep in mind the distinction between the deploy Docker environment and the application Docker images being built from the deploy container.

Examples and guidelines for setting up Dockerfile and docker-compose.yml for the deploy environment are described below:

#### `Dockerfile`
The Dockerfile should install terraform and the ecs-utils library.

Template `Dockerfile`:

```
FROM hashicorp/terraform:0.11.8 as terraform

FROM python:3.6
COPY --from=terraform /bin/terraform /usr/bin/terraform
COPY requirements.txt ./
RUN pip install -r requirements.txt
WORKDIR /home
ENV PATH "/home/utils/bin:${PATH}"
ENV PYTHONPATH "/home/utils/python:${PYTHONPATH}"
```

The `requirements.txt` file referenced is:
```
# install ecs-utils, downloads to /src/ecs-utils by default
-e git+https://github.com/harvard-vpal/ecs-app-utils.git@3.2.0#egg=ecs-utils
```

#### `docker-compose.yml`

Use a `docker-compose.yml` file to define a Docker configuration that:
* mounts AWS credential info (for accessing AWS ECR repos and for Terraform to use when applying infrastructure)
* mounts host Docker socket (build images on host)
* Invokes and passes input arguments the ecs-utils CLI as the container entrypoint (`entrypoint: python -m ecs_utils`)

Template for `docker-compose.yml`:

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
      # can be overrode in a docker-compose.override file
      - /usr/local/bin/docker:/usr/bin/docker
      # mount AWS credential info from host
      - ${HOME}/.aws/credentials:/root/.aws/credentials
    entrypoint: python -m ecs_utils
```

If applicable, optional configuration may include
* mounting ecs-app-utils python package or terraform modules (can be useful for development directly on the ecs-utils-app utilities)
* mounting app code if not pulling from github for base app image build

It may make sense to define these in a `docker-compose.override` file kept out of source control.

### Configuring application image builds
Once the deploy environment is defined, the next step is to define how the application image(s) are built, and what image repository they are pushed to. This typically is useful to keep in a `build/` subfolder.

#### `build/docker-compose.build.yml`

`ecs-utils` triggers image builds by calling `docker-compose build` on a Docker-compose file specifying build configuration for the image (or multiple images) being built as part of the application. The default location `ecs-utils` looks for the build definition is `build/docker-compose.build.yml`.

##### `${APP_TAG}`

When writing the `docker-compose.build` file, use `${APP_TAG}` for the image version when specifying image names. When invoking `docker-compose build` through `ecs-utils`, the `--tag` argument is passed to `docker-compose build` as the environment variable `APP_TAG`, which can be used to control the build image tags with `${APP_TAG}`

##### Image repository
Ensure the names for service images defined in `docker-compose.build.yml` correspond to image repositories (i.e. on AWS ECR) that exist and can be pushed to.


#### Examples

##### Example 1: web app

Example `build/docker-compose.build.yml` that
* builds a base image from the `bridge_adaptivity/` subfolder of Github repo `https://github.com/harvard-vpal/bridge-adaptivity.git` at tag `${APP_TAG}`, using the `Dockerfile_opt` Dockerfile in the repo.
* builds a custom image from the base image that uses the Dockerfile located in `app/` (relative to the compose file) to install additional libraries and copy additional settings into the image.
* pushes the app image to `12345.dkr.ecr.us-east-1.amazonaws.com/app` with image version determined by `${APP_TAG}`
* builds an nginx image using the Dockerfile in `nginx/` (relative to the compose file), which uses the app image to collect static resources and copy them into the nginx image.
* pushes the nginx image to `12345.dkr.ecr.us-east-1.amazonaws.com/nginx` with image version determined by `${APP_TAG}`


Directory structure of `build/`:
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



**`docker-compose.build.yml`**
```yaml
version: '3'
services:
  # base app image
  app_base:
    image: 12345.dkr.ecr.us-east-1.amazonaws.com/app:${APP_TAG}-base
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
        - APP_IMAGE=12345.dkr.ecr.us-east-1.amazonaws.com/app:${APP_TAG}-base
    image: 12345.dkr.ecr.us-east-1.amazonaws.com:${APP_TAG}
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.custom

  # custom nginx image build that collects static assets from app image and copies to nginx image
  nginx:
    build:
      context: nginx
      args:
        - APP_IMAGE=12345.dkr.ecr.us-east-1.amazonaws.com:${APP_TAG}
    image: 12345.dkr.ecr.us-east-1.amazonaws.com/nginx:${APP_TAG}

```

**`app/Dockerfile`**
```
# Dockerfile that derives from base app image and adds some custom settings

# Base app image:tag to use
ARG APP_IMAGE

FROM ${APP_IMAGE} as app

RUN curl -L https://github.com/remind101/ssm-env/releases/download/v0.0.3/ssm-env > /usr/local/bin/ssm-env && \
      cd /usr/local/bin && \
      echo da4bac1c1937da4689e49b01f1c85e28 ssm-env | md5sum -c && \
      chmod +x ssm-env

WORKDIR /app

# copy custom settings into desired location
COPY settings/custom.py config/settings/custom.py
COPY settings/utils.py config/settings/utils.py
COPY settings/collectstatic.py config/settings/collectstatic.py

# generate staticfiles.json even if app image is not serving static images directly
RUN python manage.py collectstatic -c --noinput --settings=config.settings.collectstatic

ENTRYPOINT ["/usr/local/bin/ssm-env"]

```

##### Examples for using local overrides

Depending on the application and local system, it may make sense to have some local/private configuration, in a [`.env`](https://docs.docker.com/compose/environment-variables/#the-env-file) or [`docker-compose.override.yml`](https://docs.docker.com/compose/extends/) file. These files can be used to provide required supplemental configuration (e.g. a github token to access a private repo) or to override certain settings in the docker-compose service definitions (e.g. override volume mounts for different host docker socket path, environment variables).

One use case is for developing directly on ecs-app-utils - mounting the source code from a local source (`/Users/me/projects/ecs-app-utils` in this example) is useful for development

`docker-compose.override.yml`
```
services:

...

  environment:
    ECS_UTILS_CONTEXT=/Users/me/projects/ecs-app-utils
```

### Configuring infrastructure with Terraform
You will need to write your own application-specific Terraform configuration. `ecs-app-utils` will look for the Terraform configuration in the `terraform/` folder of the deploy configuration repo.

The Terraform modules provided in the `terraform/` folder of this repo are designed for use as part of the application-specific Terraform infrastructure definitions, but not mandatory to use.

Typical outline for `main.tf`:
* Define custom security groups and policies
* Use a network module from `/network`
* Define web container definition (with a `template_file` data resource)
* Use a web service module
* Define other container definitions + use more service modules if applicable


#### Terraform modules

See the Repo Contents / Terraform module above for a concise outline of all available Terraform modules.

##### Network modules
Terraform modules in the `network/` folder encapsulate the load balancer, target group, routing, and other network resources. There are currently two types of network modules - the main difference being that the `public` module includes a default security policy on the load balancer that allows all incoming traffic (appropriate for a public-facing web application), and the `base` module expects a policy defined outside the module (where custom security rules can be defined) as input to the module.

##### Service modules
Service modules encapsulate the ECS service and the task definition. Depending on the type of service module, there are some additional aspects configured:

###### Load Balanced
Configures the connection to the load balancer, specified as a module input.

###### Discoverable
Relevant for internal services that are not accessed directly by web users, but rather by other services, and require an internal endpoint. Uses AWS Service Discovery to create a internal endpoint. For example: RabbitMQ.

###### Generic
Relevant for internal services that do not require connection to load balancer or a service discovery endpoint.


##### Execution role
ECS requires the use of a task execution role with permissions to access ECR repos to pull images, and access Cloudwatch for logging. This permission set is available as an AWS-managed policy `AmazonECSTaskExecutionRolePolicy`. However, additional permissions, such as allowing access to SSM parameters, may be necessary depending on the application, so the execution role Terraform module provides the ability to create an execution role with a custom policy attached as input.

#### Required Terraform outputs

The ecs-app-utils CLI requires a few outputs to be exposed in the Terraform configuration to function properly:

Required terraform outputs to expose in order to use commands:
* `cluster_name` - used in redeploy command
* `services` - map of service labels to rendered service name; used in redeploy command
* `job_task_definition_family` - used in fargate command

e.g. at the end of `main.tf` or in a separate `outputs.tf` use the following:
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

#### Create and populate a environment-specific terraform variables (`.tfvars`) file:
Example:

```
cluster_name = "alosi"
vpc_id = "vpc-337e9154"
ssl_certificate_arn = "arn:aws:acm:us-east-1:12345:certificate/abc-123-def"
hosted_zone = "example.io."
domain_name = "stage.engine.vpal.io"
env_label = "stage"
project = "engine"
short_project_label = "engine"
app_image = "12345.dkr.ecr.us-east-1.amazonaws.com/engine/app:latest"
nginx_image = "12345.dkr.ecr.us-east-1.amazonaws.com/engine/nginx:latest"
DJANGO_SETTINGS_MODULE = "config.settings"
log_group_name = "/ecs/engine/stage"

```

### CLI entrypoint
For convenience when calling the CLI, it is recommended to create a `bin/deploy` executable that can be used to invoke and pass CLI commands/arguments to the docker-compose environment file. This shortens the command used to call the CLI from `docker-compose -f {{docker-compose location}} run --rm deploy ...` to `bin/deploy ...`

`bin/deploy` contents:
```
#!/usr/bin/env bash

docker-compose -f docker-compose.yml run --rm deploy "$@"
```
Ensure the file has the right permissions for execution, e.g. `chmod a+x bin/deploy`


## Usage

### Available CLI commands
These commands assume a `bin/deploy` executable has been set up to invoke and pass arguments to the CLI.

```bash
# Build images with current app code and tag images with 'latest'
bin/deploy build
```
```bash
# Checkout the app code with the specified version and tag image with that tag
bin/deploy build --tag 1.0.0
```
```bash
# Push images with the specified tag to ECR repositories
bin/deploy push --tag 1.0.0
```
```bash
# Run 'terraform plan' with specified image tag against 'dev' environment
bin/deploy plan --tag 1.0.0 --env dev
```
```bash
# Run 'terraform apply' with specified image tag against 'dev' environment
bin/deploy apply --tag 1.0.0 --env dev
```
```bash
# Build, push, and apply
bin/deploy all --tag 1.0.0 --env dev
```
```bash
# Redeploy services (force restart of services, even if no config changes)
bin/deploy redeploy --env dev web worker
```

### First-time setup
There are a few steps required on first usage of the `ecs-app-utils` framework for an application.

#### Create and initialize terraform workspaces

For each environment, create the Terraform workspace and initialize the modules.

Example for an environment named `dev`:

Create workspace `dev`:
```
bin/deploy create --env dev
```

Initialize modules in `dev`:
```
bin/deploy init --env dev
```

#### Running initial Terraform apply

When applying infrastructure for the first time, it takes a while to create the load balancer, so downstream resources may not be created due to a "Load balancer not found" error. To resolve this, just run the `apply` command again.


### Typical workflow
* Make a code change
* Commit to git
* Tag commit
* Push commit and tag to Github
* Build image from tag
* Push image to ECR
* Apply image version on ECS environment
