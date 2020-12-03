import unittest, os, random, boto3, botocore
from yac.lib.stack import get_ec2_sgs

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.stack_name = "demos-dev" # raw_input("Input stack name >> ")
        cls.search_string = "demos-dev-asg-esg" # raw_input("Input sg search string >> ")

    def test_get_ec2_sgs(self): 

        sgs = get_ec2_sgs(self.stack_name, self.search_string)

        self.assertTrue(len(sgs)==1)

    def test_add_sgs_ingress(self): 

        sgs = get_ec2_sgs(self.stack_name, self.search_string)

        errors = True

        if len(sgs)==1:

            sg = sgs[0]

            ip_permissios = {
                "IpProtocol": 'tcp',
                "FromPort": 123,
                "ToPort": 123,          
                "IpRanges": [{
                    "CidrIp": '10.0.0.0/8',
                }]
            }

            # add ingress on port 123
            try:
                
                client = boto3.client('ec2')
                sgs = client.authorize_security_group_ingress(GroupId = sg['GroupId'],
                                                IpPermissions=[ip_permissios])
            except botocore.exceptions.ClientError as e:
                no_errors = False
                print(e) 

            # remove ingress on port 123
            try:
                
                client = boto3.client('ec2')
                sgs = client.revoke_security_group_ingress(GroupId = sg['GroupId'],
                                                IpPermissions=[ip_permissios])
            except botocore.exceptions.ClientError as e:
                no_errors = False
                print(e)
                
        self.assertTrue(no_errors)
