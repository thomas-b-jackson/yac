import unittest, os, json
from jsonschema import ValidationError
from yac.lib.params import Params
from yac.lib.makers.ami import AMI

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "name": "gitlab",
          "type": "ami",
          "profile": "nonprod",
          "packer-file": "packer/gitlab.json",
          "Secrets": {
            "datadog-api-key": {
              "comment": "Allows Datadog agent to auth into Datadog HQ",
              "source": "main",
              "lookup": "datadog_api_key"
            }
          }
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
          inputs = AMI(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_bad(self):

        serialized_obj = {
          "name": "gitlab",
          "type": "ami",
          "profil": "nonprod",
          "packer-file": "packer/gitlab.json",
          "Secrets": {
            "datadog-api-key": {
              "comment": "Allows Datadog agent to auth into Datadog HQ",
              "source": "main",
              "lookup": "datadog_api_key"
            }
          }
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
          inputs = AMI(serialized_obj)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)