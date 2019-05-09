import os
import logging
import json
import subprocess
from subprocess import run
import docker
from git import Repo, TagReference, Head
from contextlib import contextmanager
import boto3
from .fargate import FargateTask


logger = logging.getLogger(__name__)

# relative path containing terraform config
TERRAFORM_WORKING_DIRECTORY = os.environ.get('TERRAFORM_DIRECTORY', 'terraform')


def aws_ecr_login():
    login_cmd = run(f"aws ecr get-login"
                    f" --region {os.environ['AWS_DEFAULT_REGION']}"
                    f" --no-include-email"
                    .split(), stdout=subprocess.PIPE).stdout
    run(login_cmd.split())


def build_images(tag=None):
    """
    Command: Build all images, based on definitions in build/docker-compose.build.yml
    TODO: could add argument to specify services to build
    :param tag: app tag to use
    :type tag: str
    """
    aws_ecr_login()
    run(
        f'docker-compose -f build/docker-compose.build.yml build',
        env={'APP_TAG':tag} if tag else None,
        shell=True
    )


def push_images(tag='latest'):
    """
    Push all images specified in build/docker-compose.build.yml
    
    :param tag: image tag, defaults to 'latest'
    :param tag: str, optional
    """
    aws_ecr_login()
    run(
        f'docker-compose -f build/docker-compose.build.yml push',
        env={'APP_TAG':tag} if tag else None,
        shell=True
    )


def deploy(env, tag='latest'):
    """
    Applies terraform configuration
    
    :param env: environment name
    :type env: str
    :param tag: app version tag, defaults to 'latest'
    :type tag: str
    """

    wd = TERRAFORM_WORKING_DIRECTORY
    run('terraform workspace select {}'.format(env).split(), cwd=wd)
    cmd = (f'terraform apply '
        f'-var-file=terraform.{env}.tfvars '
        f'-var app_tag={tag} ')
    run(cmd.split(), cwd=wd)


def switch_terraform_env(env):
    run(f'terraform workspace select {env}'.split(), cwd=TERRAFORM_WORKING_DIRECTORY)


def fetch_terraform_output(name, env=None):
    """
    Get terraform output variable
    :param name:
    :param env:
    :return:
    """
    if env:
        switch_terraform_env(env)
    try:
        data = json.loads(
            run(
                f'terraform output -json {name}'.split(),
                cwd=TERRAFORM_WORKING_DIRECTORY,
                universal_newlines=True,  # TODO change 'universal_newlines' to 'text' in python 3.7
                stdout=subprocess.PIPE
            ).stdout
        )
    except json.JSONDecodeError:
        raise ValueError(f'Output "{name}" not available in Terraform state')
    return data['value']


def redeploy(env, services=None):
    """
    Force redeploy of ecs services
    Assumes services are named {project_name}-{env_label}-{short_service_name}, e.g. bridge-prod-web
    :param env: environment label
    :param services: list of service names (e.g. ["web", "rabbit", "worker"] to redeploy) referenced by keys in "services" terraform output variable.
        If not specified, redeploys all services listed in "services" terraform output variable.
    """
    wd = TERRAFORM_WORKING_DIRECTORY
    run(f'terraform workspace select {env}'.split(), cwd=wd)
    cluster = fetch_terraform_output('cluster_name')
    app_tag = fetch_terraform_output('app_tag')
    service_map = fetch_terraform_output('services')
    if services is None:
        services = service_map.keys()
    for name in services:
        service = service_map[name]
        boto3.client('ecs').update_service(
            cluster=cluster,
            service=service,
            forceNewDeployment=True
        )
        print(f'Redeployed ECS service: {cluster}/{service} ({app_tag})')


def create(env):
    """
    Create and initialize new terraform workspace
    
    :param env: workspace name
    :type env: str
    """
    wd = TERRAFORM_WORKING_DIRECTORY
    run('terraform workspace new {}'.format(env).split(), cwd=wd)
    run('terraform workspace select {}'.format(env).split(), cwd=wd)
    run('terraform init'.split(), cwd=wd)


def initialize(env):
    """
    Run terraform init for workspace (to fetch modules, etc)
    
    :param env: workspace name
    :type env: str
    """
    wd = TERRAFORM_WORKING_DIRECTORY
    run('terraform workspace select {}'.format(env).split(), cwd=wd)
    run('terraform init'.split(), cwd=wd)


def fargate(cmd, tag=None, env=None):
    """
    Run something on fargate
    :param cmd: command arguments to run
    :param tag: optional app image tag to use
    :return:
    """
    if env:
        switch_terraform_env(env)
    task = FargateTask(
        command=cmd,
        container_overrides={'memory': 512},
        cluster=fetch_terraform_output('cluster_name'),
        subnets=[fetch_terraform_output('subnet_ids')[0]],
        task_definition= fetch_terraform_output('job_task_definition_family'),
        container_name='app',
        security_groups=[fetch_terraform_output('security_group')],
    )
    print(f'Running "{task.command_string}" on Fargate cluster: {task.cluster}: {task.task_id}')
    print(f'View status: https://console.aws.amazon.com/ecs/home?region=us-east-1#/clusters/{task.cluster}/tasks/{task.task_id}/details')
