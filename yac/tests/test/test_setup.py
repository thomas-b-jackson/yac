import unittest, os, random
from yac.lib.test import IntegrationTests
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_setup(self): 

        test_descriptor =  {
          "tests": [
            { "name": "my-custom",
              "description": ["custom test driver will be ignored"],
              "setup": "yac/tests/test/lib/setup_cleanup.py",
              "target": "https://www.google.com/",
              "driver": "yac/tests/lib/custom_test_pass.py"
            }
          ]
        }

        params = Params({})

        tests = IntegrationTests(test_descriptor)

        err = tests.run(params,context="",test_names=["my-custom"], setup_only=True)

        # test that the setup was called and set a param
        my_setup_param = params.get('setup-param')

        self.assertTrue(my_setup_param == 'setup-value')
        self.assertTrue(not err)

    def test_bad_setup(self): 

        test_descriptor =  {
          "tests": [
            { "name": "my-custom",
              "description": ["custom test driver will be ignored"],
              "setup": "yac/tests/does_not_exist.py",
              "target": "https://www.google.com/",
              "driver": "yac/tests/lib/custom_test_pass.py"
            }
          ]
        }

        params = Params({})

        tests = IntegrationTests(test_descriptor)

        err = tests.run(params,context="",test_names=["my-custom"], setup_only=True)

        # should return an error
        self.assertTrue(err)
