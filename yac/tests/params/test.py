import unittest, os, random, json
from yac.lib.params import Params
from jsonschema import ValidationError


class TestCase(unittest.TestCase):

    def test_params(self):

        test_parameters = {
            "ssl-cert" : {
              "value": "godzilla",
              "comment": ""
            },
            "s3_path": {
              "value": "/sets/jira/dev",
              "comment": ""
            }
        }

        # run test
        params = Params(test_parameters)

        self.assertTrue(params.get("ssl-cert") == "godzilla")


    # def test_params_incorrect_format(self):
    #     # Test poorly formed parameter object (ie doesnt satisfy params schema) throws a validation error.

    #     test_parameters = {
    #         "ssl-cert" : {
    #           "value": "godzilla",
    #           "comment": ""
    #         },
    #         "s3_path": {
    #           "value": "/sets/jira/dev"

    #         }
    #     }

    #     received_validation_error = False

    #     try:
    #         params = Params(test_parameters)

    #     except ValidationError as e:
    #         received_validation_error = True

    #     self.assertTrue(received_validation_error)
