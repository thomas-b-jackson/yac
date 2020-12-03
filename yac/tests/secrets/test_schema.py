import unittest, os
from jsonschema import ValidationError
from yac.lib.secrets import Secrets

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "wlwxgittest-token": {
            "comment": "api token for the wlwxgittest user. wrapped service alias in quotes due to jsonpath cannot do lookup for paths with a hyphen",
            "source": "main",
            "lookup": {"yac-join": [".",["wlwxgittest",
                                         "tokens",
                                        {"yac-join": ["",["\"",{"yac-ref": "service-alias"},"\""]]},
                                        {"yac-ref": "env"}]]}
          }
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            secrets = Secrets(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")

        self.assertTrue(validation_success==True)

    def test_schema_bad(self):

        # "sources" instead of "source"
        serialized_obj = {
          "wlwxgittest-token": {
            "comment": "api token for the wlwxgittest user. wrapped service alias in quotes due to jsonpath cannot do lookup for paths with a hyphen",
            "sources": "main",
            "lookup": {"yac-join": [".",["wlwxgittest",
                                         "tokens",
                                        {"yac-join": ["",["\"",{"yac-ref": "service-alias"},"\""]]},
                                        {"yac-ref": "env"}]]}
          }
        }

        # test that schema validation errors are raised
        validation_success = True
        try:
            secrets = Secrets(serialized_obj)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)