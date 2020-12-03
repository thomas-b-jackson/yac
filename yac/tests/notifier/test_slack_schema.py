import unittest, os, json
from jsonschema import ValidationError
from yac.lib.notifier.slack import SlackNotifier

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "info-channel": "myteam-pipeline",
          "warning-channel": "myteam-pipeline",
          "api-key": {"yac-ref": "slack-api-key"}
        }

        # test that doesn't throw any schema validation errors
        validation_success = True
        try:
          inputs = SlackNotifier(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_bad_info(self):

        serialized_obj = {
          "info-channels": "myteam-pipeline",
          "warning-channel": "myteam-pipeline",
          "api-key": {"yac-ref": "slack-api-key"}
        }

        # test that does throw a schema validation error
        validation_success = True
        try:
          inputs = SlackNotifier(serialized_obj)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)
