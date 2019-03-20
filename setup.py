from setuptools import setup

setup(
    name='ecs_utils',
    description='Utilities for building and deploying apps on AWS ECS',
    url='https://github.com/harvard-vpal/ecs-app-utils',
    author='Andrew Ang',
    author_email='andrew_ang@harvard.edu',
    license='Apache-2.0',
    packages=['ecs_utils'],
    install_requires=[
        'docker',
        'awscli',
        'gitpython',
        'boto3',
        'docker-compose',
    ],
    use_scm_version=True,
    setup_requires=['setuptools_scm']
)
