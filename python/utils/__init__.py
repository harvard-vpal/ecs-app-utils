import os
import subprocess
from subprocess import run
import docker
from git import Repo, TagReference, Head
from contextlib import contextmanager

# relative path containing terraform config
TERRAFORM_WORKING_DIRECTORY = 'terraform'


def get_repo(path=None):
    return Repo(path if path else os.environ['APP_REPO'])


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
    build_context = os.path.join('build/app/src', os.environ.get('APP_SUBDIR', ''))
    args = dict(
        path=build_context,
        tag='{}:{}'.format(image, tag)
    )
    if os.environ.get('APP_DOCKERFILE'):
        args['dockerfile'] = f"/home/{os.environ['APP_DOCKERFILE']}"

    print("Building image: {}:{}".format(image, tag))

    client.images.build(**args)


def build_nginx_image(tag='latest'):
    """
    Build nginx timage
    :param tag: tag to use for image uri
    :return:
    """
    client = docker.from_env()
    nginx_image = os.environ['NGINX_IMAGE']
    app_image = os.environ['APP_IMAGE']
    print("Building image: {}:{}".format(nginx_image, tag))

    client.images.build(
        path='/home/build/nginx',
        tag=f'{nginx_image}:{tag}',
        buildargs={'APP_IMAGE': f'{app_image}:{tag}'}
    )


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


def deploy(env, tag=None, apply=False):
    tag = tag or 'latest'
    wd = TERRAFORM_WORKING_DIRECTORY
    app_image = os.environ['APP_IMAGE']
    nginx_image = os.environ['NGINX_IMAGE']
    action = 'apply' if apply else 'plan'

    run('terraform workspace select {}'.format(env).split(), cwd=wd)
    run(f'terraform {action} '
        f'-var-file=terraform.{env}.tfvars '
        f'-var app_image={app_image}:{tag} '
        f'-var nginx_image={nginx_image}:{tag} '
        # '-target=module.web_service '
        # '-target=module.worker_service'
        .split(), cwd=wd)


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


