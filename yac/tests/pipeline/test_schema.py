import unittest, os, json
from jsonschema import ValidationError
from yac.lib.pipeline import Pipeline

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "stages": [
            {
              "name": "dev",
              "creds": ["k8s"],
              "kvps": "env:dev",
              "build-context": "nonprod",
              "tasks": ["setup"],
              "tests": ["registry","version"],
              "test-groups": ["commits"]
            },
            {
              "name": "test",
              "creds": ["k8s"],
              "kvps": "env:stage",
              "build-context": "nonprod",
              "tasks": ["setup"],
              "tests": ["registry","version"],
              "test-groups": ["commits"]
            }
          ],
          "notifications": {
            "type": "slack",
            "configs": {
              "info-channel": "myteam-pipeline",
              "warning-channel": "myteam-pipeline",
              "api-key": {"yac-ref": "slack-api-key"}
            }
          }
        }

        # test that doesn't throw any schema validation errors
        validation_success = True
        try:
          inputs = Pipeline(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_bad_name(self):

        serialized_obj = {
          "stages": [
            {
              "names": "dev",
              "creds": ["k8s"],
              "kvps": "env:dev",
              "build-context": "nonprod",
              "tasks": ["setup"],
              "tests": ["registry","version"],
              "test-groups": ["commits"]
            },
            {
              "name": "test",
              "creds": ["k8s"],
              "kvps": "env:stage",
              "build-context": "nonprod",
              "tasks": ["setup"],
              "tests": ["registry","version"],
              "test-groups": ["commits"]
            }
          ],
          "notifications": {
            "type": "slack",
            "configs": {
              "info-channel": "myteam-pipeline",
              "warning-channel": "myteam-pipeline",
              "api-key": {"yac-ref": "slack-api-key"}
            }
          }
        }

        # test that does throw a schema validation error
        validation_success = True
        try:
          inputs = Pipeline(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==False)
