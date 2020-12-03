import unittest, os, random
from yac.lib.test import IntegrationTests
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_cleanup(self):

        test_descriptor =  {
          "tests": [
            { "name": "my-custom",
              "description": ["custom test driver will be ignored"],
              "cleanup": "yac/tests/test/lib/setup_cleanup.py",
              "target": "https://www.google.com/",
              "driver": "yac/tests/lib/custom_test_pass.py"
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        params = Params({})

        err = tests.run(params,"",test_names=["my-custom"], cleanup_only=True)

        # test that the cleanup was called and set a param
        my_cleanup_param = params.get('cleanup-param')

        self.assertTrue(my_cleanup_param == 'cleanup-value')
        self.assertTrue(not err)

    def test_bad_cleanup(self): 

        test_descriptor =  {
          "tests": [
            { "name": "my-custom",
              "description": ["custom test driver will be ignored"],
              "cleanup": "yac/tests/does_not_exist.py",
              "target": "https://www.google.com/",
              "driver": "yac/tests/lib/custom_test_pass.py"
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        err = tests.run(Params({}),"",test_names=["my-custom"], cleanup_only=True)
        print(err)

        self.assertTrue(err)