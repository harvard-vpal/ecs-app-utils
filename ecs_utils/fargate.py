import os
import boto3


class FargateTask:

    def __init__(self, cluster=None, subnets=None, task_definition=None, command=None, container_overrides={},
                 container_name='app', security_groups=None):
        """
        :param output_file: item file to write to, e.g. s3://vpal-link-data/metadata/openscholar/dtingley.csv
        :param spider: name of scrapy spider to run
        :param cpu: task run cpu allocation
        :param memory_reservation: task run memory soft allocation
        :param subnets: array of subnet ids, e.g. ['subnet-123ab456']
        :param task_definition: name of ecs task definition to create task run from
        """
        self.cluster = cluster
        self.subnets = subnets
        self.task_definition = task_definition
        self.container_name = container_name
        self.security_groups = security_groups
        # self.command is list of args
        if isinstance(command, str):
            self.command = command.split()
        else:
            self.command = command
        self.container_overrides = container_overrides
        self.response = self.run()

    def build_container_override(self):
        """
        :param container_overrides: additional container override options (besides name, command; e.g. cpu, memory)
        :return:
        """
        # build container override
        return dict(name=self.container_name, command=self.command, **self.container_overrides)

    def run(self):
        """
        Run Task via AWS api call
        :return:
        """
        client = boto3.client('ecs')
        # create task
        r = client.run_task(
            cluster=self.cluster,
            taskDefinition=self.task_definition,
            launchType='FARGATE',
            overrides={
                'containerOverrides':[self.build_container_override()],
            },
            networkConfiguration={
                'awsvpcConfiguration':{
                    'subnets':self.subnets,
                    'assignPublicIp':'ENABLED',  # see step 8: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/launch_container_instance.html
                    'securityGroups':self.security_groups
                }
            }
        )
        return r

    @property
    def task_id(self):
        if not self.response:
            return None
        else:
            # x has form {cluster}/{task_id}
            x = self.response['tasks'][0]['taskArn'].partition(':task/')[2]
            return x.partition('/')[2]

    @property
    def command_string(self):
        return ' '.join(self.command)
