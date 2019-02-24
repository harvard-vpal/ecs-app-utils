import os
import logging
import subprocess
from subprocess import run
import docker
from git import Repo, TagReference, Head
from contextlib import contextmanager
import boto3

logger = logging.getLogger(__name__)

# relative path containing terraform config
TERRAFORM_WORKING_DIRECTORY = os.environ.get('TERRAFORM_DIRECTORY', 'terraform')

# Uses build/app/src as build context by default, but a relative subdirectory within app source can be specified
APP_REPO = os.environ['APP_REPO']
APP_BUILD_CONTEXT = os.environ.get('APP_BUILD_CONTEXT', 'build/app/src')
NGINX_BUILD_CONTEXT = os.environ.get('NGINX_BUILD_CONTEXT', 'build/nginx')

def get_repo(path=None):
    return Repo(path if path else APP_REPO)


def build_app_image(tag='latest'):
    """
    Env variables:
    - APP_DOCKERFILE: Dockerfile location, relative to working dir (optional)
    - APP_SUBDIR: custom app build context, relative to APP_REPO (optional)
    :param tag: tag to use for image uri
    :return:
    """
    client = docker.from_env()
    image = os.environ['APP_IMAGE']
    # Uses build/app/src as build context by default, but a relative subdirectory within app source can be specified
    args = dict(
        path=APP_BUILD_CONTEXT,
        tag='{}:{}'.format(image, tag)
    )
    if os.environ.get('APP_DOCKERFILE'):
        args['dockerfile'] = f"/home/{os.environ['APP_DOCKERFILE']}"

    print("Building image: {}:{}".format(image, tag))

    try:
        client.images.build(**args)
    except docker.errors.BuildError as e:
        for line in e.build_log:
            if 'stream' in line:
                logger.error(line['stream'].strip())
        raise


def build_nginx_image(tag='latest'):
    """
    Build nginx image
    :param tag: tag to use for image uri
    :return:
    """
    client = docker.from_env()
    nginx_image = os.environ['NGINX_IMAGE']
    app_image = os.environ['APP_IMAGE']
    print("Building image: {}:{}".format(nginx_image, tag))

    try:
        client.images.build(
            path=NGINX_BUILD_CONTEXT,
            tag=f'{nginx_image}:{tag}',
            buildargs={'APP_IMAGE': f'{app_image}:{tag}'}
        )
    except docker.errors.BuildError as e:
        for line in e.build_log:
            if 'stream' in line:
                logger.error(line['stream'].strip())
        raise


def build_images(tag=None):
    if not tag:
        tag = 'latest'
        build_app_image(tag)
    else:
        with checkout_context(tag):
            build_app_image(tag)
    build_nginx_image(tag)


def aws_ecr_login():
    login_cmd = run(f"aws ecr get-login"
                    f" --region {os.environ['AWS_DEFAULT_REGION']}"
                    f" --no-include-email"
                    .split(), stdout=subprocess.PIPE).stdout
    run(login_cmd.split())


def push_images(tag='latest'):
    aws_ecr_login()
    print("Pushing app image...")
    client = docker.from_env()
    client.images.push(
        f"{os.environ['APP_IMAGE']}",
        tag=tag
    )
    print("Pushing nginx image...")
    client.images.push(
        f"{os.environ['NGINX_IMAGE']}",
        tag=tag
    )


def deploy(env, tag=None):
    tag = tag or 'latest'
    wd = TERRAFORM_WORKING_DIRECTORY
    app_image = os.environ['APP_IMAGE']
    nginx_image = os.environ['NGINX_IMAGE']
    action = 'apply'  # vs plan

    run('terraform workspace select {}'.format(env).split(), cwd=wd)
    run(f'terraform {action} '
        f'-var-file=terraform.{env}.tfvars '
        f'-var app_image={app_image}:{tag} '
        f'-var nginx_image={nginx_image}:{tag} '
        .split(), cwd=wd)


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

    data = json.loads(
        run(
            f'terraform output -json {name}'.split(),
            cwd=TERRAFORM_WORKING_DIRECTORY,
            universal_newlines=True,  # TODO change 'universal_newlines' to 'text' in python 3.7
            stdout=subprocess.PIPE
        ).stdout
    )
    return data['value']


def redeploy(env):
    """
    Force redeploy of ecs web service
    TODO: redeploy of multiple services if applicable, or subsets
    """
    wd = TERRAFORM_WORKING_DIRECTORY
    run(f'terraform workspace select {env}'.split(), cwd=wd)
    # TODO change 'universal_newlines' to 'text' in python 3.7
    cluster = run('terraform output cluster_name'.split(), cwd=wd, universal_newlines=True, stdout=subprocess.PIPE).stdout.strip()
    service = run('terraform output service_name'.split(), cwd=wd, universal_newlines=True, stdout=subprocess.PIPE).stdout.strip()
    boto3.client('ecs').update_service(
        cluster=cluster,
        service=service,
        forceNewDeployment=True
    )
    print(f'Redeployed ECS service: {cluster}{service}')


def initialize(env):
    wd = TERRAFORM_WORKING_DIRECTORY
    run('terraform workspace new {}'.format(env).split(), cwd=wd)
    run('terraform workspace select {}'.format(env).split(), cwd=wd)
    run('terraform init'.split(), cwd=wd)


def get_tag(commit, repo_path=None):
    """
    Get the first tag that matches the commit. Returns None if no tag found that matches commit.
    :param commit: commit hash
    :return: tag name or None
    :rtype: str
    """
    repo = get_repo(repo_path)
    tag_name = next((tag.name for tag in repo.tags if tag.commit.hexsha == commit), None)
    return tag_name


def get_current_ref(repo_path=None):
    """
    Get current branch, tag, or commit for git repo
    :param repo_path: git repository path
    :return: reference
    :rtype: str
    """
    repo = get_repo(repo_path)
    # branch
    if not repo.head.is_detached:
        return repo.head.reference.name
    # tag if possible, or commit
    else:
        return get_tag(repo.head.commit) or repo.head.commit.hexsha


def checkout(ref, repo_path=None):
    """
    Checkout a repo to the state specified by ref
    :param ref: branch name, tag, or commit
    :type ref: str
    :param repo_path: git repository path
    :type repo_path: str
    """
    repo = get_repo(repo_path)
    r = repo.refs[ref] if ref in repo.refs else None
    if isinstance(r, Head):
        # branch
        r.checkout()
    if isinstance(r, TagReference):
        # tag
        repo.git.checkout(f'tags/{ref}')
    else:
        # commit etc
        repo.git.checkout(ref)


@contextmanager
def checkout_context(target_ref, repo_path=None):
    """
    Context manager to check out a git repo to a specified branch, tag, or commit
    :param target_ref: branch name, tag, or commit hash to checkout
    :type target_ref: str
    :param repo_path: git repository path
    :type repo_path: str
    """
    current_ref = get_current_ref(repo_path)
    try:
        checkout(target_ref, repo_path)
        print(f"Checked out {target_ref}")
        yield
    finally:
        print(f"Checked out {current_ref}")
        checkout(current_ref, repo_path)


def fargate(cmd, tag=None):
    """
    Run something on fargate
    :param cmd: command arguments to run
    :param tag: optional app image tag to use
    :return:
    """
    print(f'executing fargate command {cmd}')
