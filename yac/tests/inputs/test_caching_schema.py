import unittest, os, json
from jsonschema import ValidationError
from yac.lib.params import Params
from yac.lib.inputs import InputsCacher

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "enabled": True
        }

        # test that the inputs doesn't throw any schema validation errors
        validation_success = True
        try:
          inputs = InputsCacher(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_bad_key(self):

        serialized_obj = {
          "path": "something"
        }

        # test that the a schema validation errors is raised
        # do to the kee attribute
        validation_success = True
        try:
          inputs = InputsCacher(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print(e)

        self.assertTrue(validation_success==False)
