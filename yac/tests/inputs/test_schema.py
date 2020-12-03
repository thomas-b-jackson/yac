import unittest, os, json
from jsonschema import ValidationError
from yac.lib.params import Params
from yac.lib.input import Input

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
          "conditions": {
            "kvps": "env:dev"
          }
        }

        # test that the inputs doesn't throw any schema validation errors
        validation_success = True
        try:
          inputs = Input(serialized_input)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_bad_key(self):

        serialized_input = {
          "kee": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
          "conditions": {
            "kvps": "env:dev"
          }
        }

        # test that the a schema validation errors is raised
        # do to the kee attribute
        validation_success = True
        try:
          inputs = Input(serialized_input)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==False)

    def test_schema_bad_kvps(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
          "conditions": {
            "kvp": "env:dev"
          }
        }

        # test that the a schema validation errors is raised
        # do to the kee attribute
        validation_success = True
        try:
          inputs = Input(serialized_input)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==False)