import unittest, os, json
from jsonschema import ValidationError
from yac.lib.params import Params
from yac.lib.test import IntegrationTests

class TestCase(unittest.TestCase):

    def test_schema_itest_good(self):

        # define a well-formed integration test
        test_descriptor = {
          "results-store": {
            "type": "s3",
            "path": ""
          },
          "target-map": {
            "comment": "targets for integration tests",
            "gitlab": {"yac-join": ["",["https://",
                {"yac-map": ["gitlab-cname-map","env"]}, ".",
                {"yac-map": ["hosted-zone-map","account-alias"]}]]}
          },
          "tests": [
            {
              "name": "read-google",
              "description": ["assert against aggregated latency stats"],
              "setup": "optional",
              "cleanup": "optional",
              "target": "gitlab",
              "artillery": {
                "config": "yac/tests/test/vectors/artillery/read_google.json",
                "assertions": {
                  "p95_sec": "10",
                  "median_sec": "7",
                  "error_count": "0",
                  "status": ["200"]
                }
              }
            },
            {
              "name": "read-db",
              "description": ["assert against db availability"],
              "target": "rds",
              "setup": "optional",
              "cleanup": "optional",
              "driver": "yac/tests/test/vectors/custom/test_db_read.py"
            }
          ]
        }

        # test that the test doesn't throw any errors
        validation_success = True
        try:
          tests = IntegrationTests(test_descriptor)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_itest_bad_type(self):

        # define a poorly-formed integration test by making status code an
        # int rather than a string
        test_descriptor = {
          "results-store": {
            "type": "s3",
            "path": ""
          },
          "tests": [
            {
              "name": "read-google",
              "description": ["assert against aggregated latency stats"],
              "setup": "optional",
              "cleanup": "optional",
              "target": "https://www.google.com/",
              "artillery": {
                "config": "yac/tests/test/vectors/artillery/read_google.json",
                "assertions": {
                  "p95_sec": "10",
                  "median_sec": "7",
                  "error_count": "0",
                  "status": [200]
                }
              }
            },
            {
              "name": "read-db",
              "description": ["assert against db availability"],
              "target": "https://www.google.com/",
              "setup": "optional",
              "cleanup": "optional",
              "driver": "yac/tests/test/vectors/custom/test_db_read.py"
            }
          ]
        }

        # test that the test throws a validation errors
        validation_success = True
        validation_err_msg_success = False
        try:
          tests = IntegrationTests(test_descriptor)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)

    def test_schema_itest_no_tests(self):

        # define a poorly-formed integration test by failing to specify
        # any tests or test groups
        test_descriptor = {
          "results-store": {
            "type": "s3",
            "path": ""
          }
        }

        # test that the test throws a validation errors
        validation_success = True
        try:
          tests = IntegrationTests(test_descriptor)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)

    def test_schema_itest_extra_param(self):

        # define a poorly-formed integration test by adding an extra
        # param (the "descriptions" attribute under "tests")
        test_descriptor = {
          "tests": [
            {
              "name": "read-google",
              "descriptions": ["assert against aggregated latency stats"],
              "target": "https://www.google.com/",
              "artillery": {
                "config": "yac/tests/test/vectors/artillery/read_google.json",
                "assertions": {
                  "p95_sec": "10",
                  "median_sec": "7",
                  "error_count": "0",
                  "status": ["200"]
                }
              }
            }
          ]
        }

        # test that the test throws a validation errors
        validation_success = True
        validation_err_msg_success = False
        try:
          tests = IntegrationTests(test_descriptor)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            validation_err_msg_success = "Additional properties are not allowed ('descriptions' was unexpected)" in e.message
            # print e

        self.assertTrue(validation_success==False)
        self.assertTrue(validation_err_msg_success==True)

    def test_schema_test_target(self):

        # define a well-formed test with a specific target
        test_descriptor = {
          "tests": [
            {
              "name": "read-google",
              "description": ["assert against aggregated latency stats"],
              "target": "https://www.google.com",
              "setup": "optional",
              "cleanup": "optional",
              "artillery": {
                "config": "yac/tests/test/vectors/artillery/read_google.json",
                "assertions": {
                  "p95_sec": "10",
                  "median_sec": "7",
                  "error_count": "0",
                  "status": ["200"]
                }
              }
            }
          ]
        }

        # test that the test doesn't throw any errors
        validation_success = True
        try:
          tests = IntegrationTests(test_descriptor)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_test_no_target(self):

        # define a poorly-formed integration test by failing
        # to include a target
        test_descriptor = {
          "tests": [
            {"name": "read-google",
            "description": ["assert against aggregated latency stats"],
            "setup": "optional",
            "cleanup": "optional",
            "artillery": {
              "config": "yac/tests/test/vectors/artillery/read_google.json",
              "assertions": {
                "p95_sec": "10",
                "median_sec": "7",
                "error_count": "0",
                "status": [200]
              }
            }
          }
          ]
        }

        # test that the test throws a validation error
        validation_success = True
        validation_err_msg_success = False
        try:
          tests = IntegrationTests(test_descriptor)
        except ValidationError as e:
            validation_success = False
            validation_err_msg_success = "'target' is a required property" in e.message

        self.assertTrue(validation_success==False)
        self.assertTrue(validation_err_msg_success==True)