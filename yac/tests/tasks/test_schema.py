import unittest, os, json
from jsonschema import ValidationError
from yac.lib.task import Tasks

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = [
          {
            "name": "backup",
            "description": "take a snapshot backup of the postgres data",
            "module": "lib/backup.py"
          },
          {
            "name": "restore",
            "description": "restore DB from the most recent backup or from a specific point-in-time",
            "module": "yac/tests/tasks/vectors/sample.py",
            "Inputs": [
              {
                "key": "env",
                "title": "Environment",
                "type": "string",
                "help":  "The environment to build stack for",
                "required": True
              }
            ]
          }
        ]

        # test that doesn't throw any schema validation errors
        validation_success = True
        try:
          inputs = Tasks(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_bad_name(self):

        serialized_obj = [
          {
            "names": "backup",
            "description": "take a snapshot backup of the postgres data",
            "module": "lib/backup.py"
          },
          {
            "name": "restore",
            "description": "restore DB from the most recent backup or from a specific point-in-time",
            "module": "yac/tests/tasks/vectors/sample.py",
            "Inputs": [
              {
                "key": "env",
                "title": "Environment",
                "type": "string",
                "help":  "The environment to build stack for",
                "required": True
              }
            ]
          }
        ]

        # test that does throw a schema validation error
        validation_success = True
        try:
          inputs = Tasks(serialized_obj)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)
