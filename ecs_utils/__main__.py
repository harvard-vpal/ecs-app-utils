#!/usr/bin/env python

"""
Command line interface entrypoint for common build/deployment tasks.

Subcommands:
    create: Create terraform workspace
    init: Initialize terraform workspace (workspace must be created first)
    build: Build app and nginx images
    push: Push image to repository
    apply: Apply terraform changes (including updating app image version)
    redeploy: Force redeploy of ecs web service without changing configuration
    all: build, push and apply

Usage examples:
    deploy create --env dev
    deploy init --env dev
    deploy build --tag 1.0.0
    deploy push --tag 1.0.0
    deploy apply --tag 1.0.0 --env dev
    deploy all --tag 1.0.0 --env dev

"""

import argparse
from .commands import build_images, push_images, deploy, create, initialize, redeploy, fargate


def all(tag=None, env=None):
    """
    functionality for 'all' subcommand
    """
    build_images(tag=tag)
    push_images(tag=tag)
    deploy(env=env, tag=tag)


def create_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # parent parser with tag argument
    tag_parser = argparse.ArgumentParser(add_help=False)
    tag_parser.add_argument('--tag', type=str, help='version tag to deploy')

    # parent parser with env argument
    env_parser = argparse.ArgumentParser(add_help=False)
    env_parser.add_argument('--env', type=str, required=True, help='label of environment to deploy to')

    # create
    parser_create = subparsers.add_parser('create', parents=[env_parser], description='Create and initialize terraform workspace')
    parser_create.set_defaults(func=create)

    # init
    parser_init = subparsers.add_parser('init', parents=[env_parser], description='Reinitialize terraform workspace')
    parser_init.set_defaults(func=initialize)

    # build
    parser_build = subparsers.add_parser('build', parents=[tag_parser], description='Build image')
    parser_build.set_defaults(func=build_images)

    # push
    parser_push = subparsers.add_parser('push', parents=[tag_parser], description='Push image')
    parser_push.set_defaults(func=push_images)

    # apply
    parser_apply = subparsers.add_parser('apply', parents=[tag_parser, env_parser], description='Terraform apply')
    parser_apply.set_defaults(func=deploy)

    # redeploy
    parser_apply = subparsers.add_parser('redeploy', parents=[env_parser], description='Redeploy web service')
    parser_apply.set_defaults(func=redeploy)

    # all
    parser_all = subparsers.add_parser('all', parents=[tag_parser, env_parser], description='Build, push and terraform apply')
    parser_all.set_defaults(func=all)

    # fargate
    parser_fargate = subparsers.add_parser('fargate', parents=[tag_parser, env_parser], description='run task on fargate')
    parser_fargate.add_argument('cmd', nargs='*', help='cmd args to run via fargate')
    parser_fargate.set_defaults(func=fargate)

    return parser


args = vars(create_parser().parse_args())
args.pop('func')(**args)
