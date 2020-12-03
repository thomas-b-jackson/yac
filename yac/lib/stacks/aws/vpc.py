import json, boto3, os, botocore

from yac.lib.stacks.aws.session import get_session

def get_vpcs( params,
              name_search_string=""):

    vpcs=[]
    session,err = get_session(params)

    if not err:

        try:
            ec2 = session.resource('ec2')

            vpcs = list(ec2.vpcs.filter(Filters=[{'Name':'tag:Name',
                                                  'Values':['*%s*'%name_search_string]}]))
        except botocore.exceptions.ClientError as e:
            err = e

    return vpcs, err

def get_subnet_ids( vpc,
                    azs,
                    params,
                    name_search_string=""):

    subnet_ids = []

    session,err = get_session(params)

    if not err:

        try:
            ec2 = session.resource('ec2')

            for az in azs:

                for subnet in vpc.subnets.filter(Filters=[{"Name": "availabilityZone", "Values": [az]},
                                                          {'Name':'tag:Name', 'Values':['*%s*'%name_search_string]}]):

                    subnet_ids.append(subnet.id)

        except botocore.exceptions.ClientError as e:
            err = e
    else:
        err = "error determining subnet ids: %s"%err

    return subnet_ids, err
