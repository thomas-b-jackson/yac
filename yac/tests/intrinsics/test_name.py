import unittest, os, random, json
from yac.lib.intrinsic import apply_intrinsics, IntrinsicsError
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_default_name(self):       

        params = {
          "service-alias": {"value": "jira"}, 
          "availability-zones": {"value": ["us-west-2a"]}
        }

        test_dict =  {
            "Type" : "AWS::AutoScaling::AutoScalingGroup",
            "Name" : { "yac-name" : "asg" }
        }

        updated_dict = apply_intrinsics(test_dict, 
                                        Params(params))

        name_check = updated_dict['Name'] == 'jira-asg'

        self.assertTrue(name_check)  
     
    def test_naming_convention(self):       

        params = {
            "service-alias": {
                "value": "jira"
            }, 
            "env": {
                "value": "prod"
            },
            "naming-convention": {
                "comment": "name resources using the alias followed by the environment",
                "value": {
                    "param-keys": ['service-alias','env'],
                    "delimiter": "."
                }
            }
        }

        test_dict =  {
            "Type" : "AWS::AutoScaling::AutoScalingGroup",
            "Name" : { "yac-name" : "asg" }
          }

        updated_dict = apply_intrinsics(test_dict, 
                                        Params(params))

        name_check = updated_dict['Name'] == 'jira.prod.asg'

        self.assertTrue(name_check)