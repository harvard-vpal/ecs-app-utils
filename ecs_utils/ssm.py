import boto3


def get_ssm_parameter(name):
    """
    Retrieve value of a AWS SSM Param Store parameter
    Assumes boto3 credentials are configured in environment
    :param name: parameter name
    :return: parameter value
    """
    ssm = boto3.client('ssm')
    return ssm.get_parameter(Name=name)['Parameter']['Value']
