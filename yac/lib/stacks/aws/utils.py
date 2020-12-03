import os, json, urllib.parse, boto3, subprocess
import shutil, jmespath, sys, time, imp
from botocore.exceptions import ClientError

# Get the running ec2 instances in a stack identified by stack_name
def get_running_ec2s( stack_name , name_search_string=""):

    # filters for stack_id in cloudformation tag
    filters = [{'Name':"tag:aws:cloudformation:stack-name", 'Values' : [stack_name]}]

    # if specifying a Name, filter on that name
    if name_search_string:
        filters.append({'Name':"tag:Name", 'Values' : [name_search_string]})

    #pull response with instances matching filters
    client = boto3.client('ec2')
    reservations = client.describe_instances(Filters=filters)

    # get the private or public ip address of instances that are running
    ips = jmespath.search("Reservations[?Instances[?State.Name=='running']].Instances[*]", reservations)

    # because the of the reservations in the outer layer, the search above will return
    # the IP array in a out array, e.g.
    # [['ip1'], ['ip2'], etc.]]
    # convert this to a list of strings, e.g.
    # ['ip1', 'ip2', etc.]]
    ip_str_list = []

    for ip in ips:
        if len(ip)==1:
            ip_str_list.extend(ip)

    return ip_str_list

# Get the ip addresses of ec2 instances in a stack identified by stack_name
# with a name containing name_search_string.
# If no name_search_string provided, returns IP addresses of all stack EC2 instances
def get_ec2_ips( stack_name , name_search_string="", publicIP=False):

    # filters for stack_id in cloudformation tag
    filters = [{'Name':"tag:aws:cloudformation:stack-name", 'Values' : [stack_name]}]

    # if specifying a Name, filter on that name
    if name_search_string:
        filters.append({'Name':"tag:Name", 'Values' : [name_search_string]})

    #pull response with instances matching filters
    client = boto3.client('ec2')
    instances = client.describe_instances(Filters=filters)

    # get the private or public ip address of instances that are running
    if publicIP:
        ips = jmespath.search("Reservations[?Instances[?State.Name=='running']].Instances[*].PublicIpAddress", instances)
    else:
        ips = jmespath.search("Reservations[?Instances[?State.Name=='running']].Instances[*].PrivateIpAddress", instances)

    # because the of the reservations in the outer layer, the search above will return
    # the IP array in a out array, e.g.
    # [['ip1'], ['ip2'], etc.]]
    # convert this to a list of strings, e.g.
    # ['ip1', 'ip2', etc.]]
    ip_str_list = []

    for ip in ips:
        if len(ip)==1:
            ip_str_list.extend(ip)

    return ip_str_list

def get_ec2_sgs(stack_name, name_search_string=""):

    # filters for stack_id in cloudformation tag
    filters = [{'Name':"tag:aws:cloudformation:stack-name", 'Values' : [stack_name]}]

    # if specifying a Name, filter on that name
    if name_search_string:
        filters.append({'Name':"tag:Name", 'Values' : [name_search_string]})

    #pull response with instances matching filters
    client = boto3.client('ec2')
    sgs = client.describe_security_groups(Filters=filters)

    # we need to get rid of outer array
    return sgs['SecurityGroups']

# get the RDS endpoints associated with a stack
def get_rds_endpoints( stack_name ):

    endpoints = []

    # get the resources associated with the stack
    cloudformation = boto3.client('cloudformation')
    resources = cloudformation.describe_stack_resources(StackName=stack_name)

    rds_id = ""

    if 'StackResources' in resources:

        for resource in resources['StackResources']:

            if resource['ResourceType'] == 'AWS::RDS::DBInstance':

                rds_id = resource['PhysicalResourceId']

    if rds_id:

        client = boto3.client('rds')
        instances = client.describe_db_instances(DBInstanceIdentifier=rds_id)

        # print "instances: %s"%json.dumps(instances,indent=2)

        endpoints = jmespath.search("DBInstances[*].{Address: Endpoint.Address, Port: Endpoint.Port, Status: DBInstanceStatus}", instances)

    return endpoints

# get the ECS services associated with a stack
def get_ecs_service( stack_name , name_search_string):

    to_ret={}

    # get the resources associated with the stack
    cloudformation = boto3.client('cloudformation')
    resources = cloudformation.describe_stack_resources(StackName=stack_name)

    service_id = ""
    cluster_name = ""

    if 'StackResources' in resources:

        for resource in resources['StackResources']:

            if resource['ResourceType'] == 'AWS::ECS::Service':

                if name_search_string in resource['PhysicalResourceId']:
                    service_id = resource['PhysicalResourceId']
                    #print "ecs service: %s"%service_id

            if resource['ResourceType'] == 'AWS::ECS::Cluster':

                cluster_name = resource['PhysicalResourceId']
                #print "ecs cluster: %s"%cluster_name

    if service_id and cluster_name:

        client = boto3.client('ecs')
        services = client.describe_services(cluster=cluster_name,
                                            services=[service_id])

        #print "ecs services: %s"%services
        for service in services['services']:
            if name_search_string in service['serviceName']:
                to_ret = service
                break

    return to_ret

# get the ECS services associated with a stack
def get_stack_elbs( stack_name , name_search_string):

    to_ret={}

    # get the resources associated with the stack
    cloudformation = boto3.client('cloudformation')
    resources = cloudformation.describe_stack_resources(StackName=stack_name)

    elb_id = ""

    if 'StackResources' in resources:

        for resource in resources['StackResources']:

            if resource['ResourceType'] == 'AWS::ElasticLoadBalancing::LoadBalancer':

                if name_search_string in resource['PhysicalResourceId']:
                    elb_id = resource['PhysicalResourceId']
                    break


    if elb_id:

        client = boto3.client('elb')
        elbs = client.describe_load_balancers(LoadBalancerNames=[elb_id])

        for elb in elbs['LoadBalancerDescriptions']:
            if name_search_string in elb['LoadBalancerName']:
                to_ret = elb
                break
    return to_ret

def get_ami_name(ami_id):

    ec2 = boto3.resource("ec2")
    image = ec2.Image(ami_id)
    return image.name

def get_ami(name_search_string=""):

    ec2 = boto3.resource("ec2")

    ami_list = list(ec2.images.filter(Filters=[{'Name':'tag:Name',
                                          'Values':['*%s*'%name_search_string]}]))

    return ami_list

def get_rds_instance_ids( stack_name ):

    instances_ids = []

    # get the resources associated with the stack
    cloudformation = boto3.client('cloudformation')
    resources = cloudformation.describe_stack_resources(StackName=stack_name)

    rds_id = ""

    if 'StackResources' in resources:

        for resource in resources['StackResources']:

            if resource['ResourceType'] == 'AWS::RDS::DBInstance':

                rds_id = resource['PhysicalResourceId']

    if rds_id:

        client = boto3.client('rds')
        instances = client.describe_db_instances(DBInstanceIdentifier=rds_id)

        instances_ids = jmespath.search("DBInstances[*].DBInstanceIdentifier", instances)

    return instances_ids

# get the name of the elastic cache endpoint associated with a stack
def get_cache_endpoint( stack_name ):

    endpoint = {}

    # get the resources associated with the stack
    cloudformation = boto3.client('cloudformation')
    resources = cloudformation.describe_stack_resources(StackName=stack_name)

    cache_id = ""

    if 'StackResources' in resources:

        for resource in resources['StackResources']:

            if resource['ResourceType'] == 'AWS::ElastiCache::ReplicationGroup':

                cache_id = resource['PhysicalResourceId']

    if cache_id:

        client = boto3.client('elasticache')
        response = client.describe_replication_groups(ReplicationGroupId=cache_id)

        if ('ReplicationGroups' in response and len(response['ReplicationGroups'])>0):

            this_rep_group = response['ReplicationGroups'][0]

            for node in this_rep_group['NodeGroups']:

                if 'PrimaryEndpoint' in node:

                    endpoint = node['PrimaryEndpoint']

    return endpoint

# get the subnets associated with an auto-scaling groups
def get_asg_subnet_ids( asg_name ):

    #pull response with instances matching filters
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])

    if response['AutoScalingGroups']:
        asg = response['AutoScalingGroups'][0]
    else:
        asg = {}

    subnet_ids = []

    if asg:
        subnet_id_str = asg['VPCZoneIdentifier']
        subnet_ids = subnet_id_str.split(',')

    return subnet_ids

# get the iam role associated with an auto-scaling groups
def get_stack_iam_role( params ):

    asg_name = get_resource_name(params,'asg')

    #pull response with instances matching filters
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])

    if response['AutoScalingGroups']:
        asg = response['AutoScalingGroups'][0]
        launchConfigName = asg['LaunchConfigurationName']
    else:
        launchConfigName = ""

    iam_role = ""

    if launchConfigName:
        response = client.describe_launch_configurations(LaunchConfigurationNames=[launchConfigName])

        if response['LaunchConfigurations']:
            iam_role = response['LaunchConfigurations'][0]['IamInstanceProfile']

    return iam_role

# get the ssh key associated with an auto-scaling groups
def get_stack_ssh_keys( params ):

    asg_name = get_resource_name(params,'asg')

    #pull response with instances matching filters
    client = boto3.client('autoscaling')
    response = client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])

    if response['AutoScalingGroups']:
        asg = response['AutoScalingGroups'][0]
        launchConfigName = asg['LaunchConfigurationName']
    else:
        launchConfigName = ""

    ssh_key = ""

    if launchConfigName:
        response = client.describe_launch_configurations(LaunchConfigurationNames=[launchConfigName])

        if response['LaunchConfigurations']:
            ssh_key = response['LaunchConfigurations'][0]['KeyName']

    return ssh_key

# get the ssl cert associated with an elb
def get_stack_ssl_cert( params ):

    ielb_name = get_resource_name(params,'i-elb')
    eelb_name = get_resource_name(params,'e-elb')

    #pull response with instances matching filters
    client = boto3.client('elb')
    response = client.describe_load_balancers(LoadBalancerNames=[ielb_name,eelb_name])

    if response['LoadBalancerDescriptions']:
        elb = response['LoadBalancerDescriptions'][0]
    else:
        elb = {}

    ssl_cert = ""

    if elb:
        ssl_certs = jmespath.search('[*].Listener.SSLCertificateId',elb['ListenerDescriptions'])
        if (ssl_certs and len(ssl_certs)==1):
            ssl_cert = ssl_cert[0]

    return ssl_cert

# returns true if an existing stack has external (public) access
def stack_has_external_access( params ):

    external_access = False

    eelb_name = get_resource_name(params,'e-elb')

    #pull response with instances matching filters
    client = boto3.client('elb')
    response = client.describe_load_balancers(LoadBalancerNames=[eelb_name])

    if response['LoadBalancerDescriptions']:
        elb = response['LoadBalancerDescriptions'][0]
    else:
        elb = {}

    # if the e-elb was found, stack provides external access
    if elb:
        external_access = True

    return external_access

# get vpc associated with an existing stack
def get_stack_vpc( stack_name ):

    vpc_id = ""

    if stack_name:

        # get the stack
        cloudformation = boto3.client('cloudformation')

        try:
            stack = cloudformation.describe_stacks(StackName=stack_name)

            # get the first stack's 'stack id'
            stack_id = stack['Stacks'][0]['StackId']

            # filters for stack_id in cloudformation tag
            filters = [{'Name':"tag:aws:cloudformation:stack-id", 'Values' : [stack_id]}]

            #pull response with instances matching filters
            client = boto3.client('ec2')

            reservations = client.describe_instances(Filters=filters)

            intances = jmespath.search('Reservations[*].Instances',reservations)

            if len(intances)>=1:

                # use the vpd id of the first instance
                # print intances[0][0]
                vpc_id = intances[0][0]['VpcId']

                vpcs = client.describe_vpcs(VpcIds=[vpc_id])

                if 'Vpcs' in vpcs and len(vpcs['Vpcs'])==1:
                    vpc =  vpcs['Vpcs'][0]
                    vpc_id = vpc["VpcId"]

        except ClientError as e:
            print("existing stack not found")

        return vpc_id

# get the subnets associated with an internal load balancer
def get_elb_subnet_ids( load_balancer_name ):

    #pull response with instances matching filters
    client = boto3.client('elb')
    response = client.describe_load_balancers(LoadBalancerNames=[load_balancer_name])

    if response['LoadBalancerDescriptions']:
        elb = response['LoadBalancerDescriptions'][0]
    else:
        elb = {}

    subnet_ids = []

    if elb:
        subnet_ids = elb['Subnets']

    return subnet_ids

# get the value from a tag
def get_stack_tag_value( stack_name , stack_tag_name ):

    client = boto3.client('cloudformation')

    response = client.describe_stacks(StackName=stack_name)

    if response['Stacks']:
        stack = response['Stacks'][0]
    else:
        stack = {}

    value = ""

    if (stack and 'Tags' in stack):
        for param in stack['Tags']:
            if param['Key'] == stack_tag_name:
                value = param['Value']

    return value

def stop_service_blocking(stack_name, name_search_string):

    ecs_service = get_ecs_service(stack_name, name_search_string)

    if ecs_service and ecs_service['runningCount'] == 1:

        print("Stopping the %s service ..."%ecs_service['serviceName'])

        # stop the service by setting the desired count to 0
        client = boto3.client('ecs')
        client.update_service(cluster=ecs_service['clusterArn'],
                              service=ecs_service['serviceName'],
                              desiredCount=0)

        timer_start=dt.datetime.now()

        # wait for the running count to change to "0"
        while ( ecs_service['runningCount'] != 0 ):

            now=dt.datetime.now()
            elapsed_secs = (now-timer_start).seconds
            sys.stdout.write('\r')
            msg = ("After %s seconds, the service is still running ...")%(elapsed_secs)
            sys.stdout.write(msg)
            sys.stdout.flush()

            # sleep for 5 seconds then check service state again
            time.sleep(5)

            # check the state of the service
            ecs_service = get_ecs_service(stack_name, name_search_string)

        # print an empty line to insert a cr
        print("")

def start_service(stack_name, name_search_string):

    ecs_service = get_ecs_service(stack_name, name_search_string)

    if ecs_service and ecs_service['runningCount'] == 0:

        # stop the service by setting the desired count to 0
        client = boto3.client('ecs')
        client.update_service(cluster=ecs_service['clusterArn'],
                              service=ecs_service['serviceName'],
                              desiredCount=1)