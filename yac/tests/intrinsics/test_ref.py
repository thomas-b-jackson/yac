import unittest, os, random, json
from yac.lib.intrinsic import apply_intrinsics, IntrinsicsError
from yac.lib.params import Params


class TestCase(unittest.TestCase):

    # test when a list contains a list
    def test_list_of_lists(self): 
        
        params = {
            "ssl-cert" : {
              "type" : "string",
              "value": "godzilla"
            },
            "s3_path": {
               "type" : "boolean",
                "value": "/sets/jira/dev"           
            }
        }

        test_dict = {"Listeners": [
            {
              "InstancePort": {
                "Ref": "WebServerPort"
              },
              "SSLCertificateId": {
                "Fn::Join": [
                  "",
                  [
                    "arn:aws:iam::",
                    {
                      "Ref": "AWS::AccountId"
                    },
                    ":server-certificate",
                    "/",
                    {
                      "yac-ref": "ssl-cert"
                    }
                  ]
                ]
              },
              "LoadBalancerPort": "443",
              "Protocol": "HTTPS",
              "InstanceProtocol": "HTTPS"
            }
          ]
        }

        # run test
        updated_dict = apply_intrinsics(test_dict, Params(params))      

        updated_dict_str = json.dumps(updated_dict)
        
        ref_check = "godzilla" in updated_dict_str

        self.assertTrue(ref_check) 
        
    # test refs and joins
    def test_intrinsics(self): 
        
        params = {
            "comment": "the following parameters are populated by yac automatically, and can be referenced using {'yac_param': 'param-name'}",
            "cpu" : {
              "type" : "integer",
              "value": 3
            },
            "protocol" : {
              "type" : "string",
              "value": "http"
            },
            "essential": {
               "type" : "boolean",
               "value": False           
            },
            "s3_path": {
               "type" : "boolean",
                "value": "/sets/jira/dev"           
            }
        }

        test_dict = {
            "containers": [
              {
                "name": "jira", 
                "image": "nordstromsets/jira:6.3.17",
                "command": [],
                "cpu": {"yac-ref": "cpu"},
                "essential": {"yac-ref": "essential"},
                "volumesFrom": {
                    "comment": "testing",
                    "value": {"yac-join" : [ "/", [ 
                             {"yac-ref": "s3_path"},
                              "backups.json" ]]}
                },
                "memory": 2148,
                "disableNetworking": False,                
                "portMappings": [
                  {
                    "hostPort": 80,
                    "containerPort": 8090,
                    "protocol": {"yac-ref": "protocol"}
                  }
                ],
              },
              {
                "name": "confluence", 
                "image": "nordstromsets/confluence:6.3.17",
                "command": [],
                "cpu": {"yac-ref": "cpu"},
                "essential": {"yac-ref": "essential"},
                "volumesFrom": {
                    "comment": "testing",
                    "value": {"yac-join" : [ "/", [ 
                             {"yac-ref": "s3_path"},
                              "backups.json" ]]}
                },
                "memory": 2148,
                "disableNetworking": False,                
                "portMappings": [
                  {
                    "hostPort": 80,
                    "containerPort": 8090,
                    "protocol": {"yac-ref": "protocol"}
                  }
                ],
              }              
            ]
        }

        test_dict2 = {"this": {"that": "other"}, 
                     "list": [1,2,3],
                     "scalar": "test"
                     }

        # run test
        updated_dict = apply_intrinsics(test_dict, Params(params))

        self.assertTrue(len(updated_dict['containers']) == 2)
        self.assertTrue(updated_dict['containers'][0]['cpu'] == 3)
        self.assertTrue(updated_dict['containers'][0]['portMappings'][0]['protocol'] == "http")
        self.assertTrue(updated_dict['containers'][0]['essential'] == False)
        self.assertTrue( updated_dict['containers'][0]['volumesFrom']['value'] == "/sets/jira/dev/backups.json")

    # test join where one element is empty
    def test_null_join(self): 
        
        params = {
            "suffix" : {
              "type" : "string",
              "value": ""
            },
            "s3_path": {
               "type" : "boolean",
                "value": "/sets/jira/dev"           
            }
        }

        test_dict = {
            "volumesFrom": {
                "comment": "testing",
                "value": {"yac-join" : [ "/", [ 
                         {"yac-ref": "s3_path"},
                         {"yac-ref": "suffix"},
                          "backups.json" ]]}
            }
        }

        # run test
        updated_dict = apply_intrinsics(test_dict, Params(params))

        join_check = updated_dict['volumesFrom']['value'] == "/sets/jira/dev/backups.json"

        self.assertTrue(join_check)  


    # test when a dictionary references a param that doesn't exist
    def test_reference_error(self): 
        
        params = {
            "suffix" : {
              "type" : "string",
              "value": ""
            },
            "s3_path": {
               "type" : "boolean",
                "value": "/sets/jira/dev"           
            }
        }

        test_dict = {
            "volumesFrom": {
                "comment": "testing",
                "value": {"yac-ref": "suffi"}
            }
        }

        error_received=False
        try:
            updated_dict = apply_intrinsics(test_dict, Params(params))
        except IntrinsicsError as e:
            error_received = True
            print(json.dumps(test_dict,indent=2))
        
        self.assertTrue(error_received)        