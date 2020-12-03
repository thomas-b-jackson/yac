import unittest, os
from jsonschema import ValidationError
from yac.lib.stacks.aws.stack import AWSStack

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "type": "aws-cloudformation",
          "Conditions": {},
          "Resources": {},
          "Parameters": {},
          "BootFiles": {
            "files": [{
              "src": "config/gitlab-1.rb",
              "dest": {"yac-join" : [ "/", [
                         "s3:/",
                        {"yac-ref": "s3-bucket-map"},
                        {"yac-ref": "service-alias"},
                        {"yac-ref": "env"},
                         "gitlab-1.rb" ]]}
              }
            ],
            "directories": [
              {
                "src": "config/datadog",
                "dest": {"yac-join" : [ "/", [
                           "s3:/",
                          {"yac-ref": "s3-bucket-map"},
                          {"yac-ref": "service-alias"},
                          {"yac-ref": "env"},
                           "datadog" ]]}
              }
            ]
          },
          "ParameterMapping": {
            "MasterUserPassword": {
              "comment": "RDS doesn't allow this to be updated on stack updates (thus the cf param is immutable)",
              "value": {"yac-ref": "rds-master-pwd"},
              "immutable": True
            }
          }
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            stack = AWSStack(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")

        self.assertTrue(validation_success==True)

    def test_schema_bad(self):

        # BootFiles.files[0].srcc instead of src
        serialized_obj = {
          "type": "aws-cloudformation",
          "Conditions": {},
          "Resources": {},
          "Parameters": {},
          "BootFiles": {
            "files": [{
              "srcc": "config/gitlab-1.rb",
              "dest": {"yac-join" : [ "/", [
                         "s3:/",
                        {"yac-ref": "s3-bucket-map"},
                        {"yac-ref": "service-alias"},
                        {"yac-ref": "env"},
                         "gitlab-1.rb" ]]}
              }
            ],
            "directories": [
              {
                "src": "config/datadog",
                "dest": {"yac-join" : [ "/", [
                           "s3:/",
                          {"yac-ref": "s3-bucket-map"},
                          {"yac-ref": "service-alias"},
                          {"yac-ref": "env"},
                           "datadog" ]]}
              }
            ]
          },
          "ParameterMapping": {
            "MasterUserPassword": {
              "comment": "RDS doesn't allow this to be updated on stack updates (thus the cf param is immutable)",
              "value": {"yac-ref": "rds-master-pwd"},
              "immutable": True
            }
          }
        }

        # test that a schema validation errors is raised
        validation_success = True
        try:
            stack = AWSStack(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")

        self.assertTrue(validation_success==False)