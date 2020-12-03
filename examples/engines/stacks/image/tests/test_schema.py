import unittest, os
from jsonschema import ValidationError
from yac.lib.stacks.gcp.stack import GCPStack

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "type": "gcp-cloudmanager",
          "Resources": {}
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            stack = GCPStack(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")

        self.assertTrue(validation_success==True)

    def test_schema_bad(self):

        serialized_obj = {
          "type": "gcp-cloudmanager",
          "Resource": {}
        }

        # test that a schema validation error is raised
        validation_success = True
        try:
            stack = GCPStack(serialized_obj)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)