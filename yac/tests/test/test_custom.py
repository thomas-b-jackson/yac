import unittest
from yac.lib.params import Params
from yac.lib.test import IntegrationTests

class TestCase(unittest.TestCase):

    def test_custom(self):

        test_descriptor =  {
          "tests": [
            { "name": "my-custom",
              "description": ["a custom test driver"],
              "target": "https://www.google.com/",
              "driver": "yac/tests/test/lib/custom_test_pass.py"
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        tests.run(Params({}),"",test_names=['my-custom'])

        test_results = tests.get_results()

        # test that the pass count is 1
        self.assertTrue(len(test_results.get_passing_tests()) == 1)

    # test that we can select a specific test
    def test_custom_select(self):

        test_descriptor =  {
          "tests": [
            { "name": "my-custom-1",
              "description": ["a custom test driver"],
              "target": "https://www.google.com/",
              "driver": "yac/tests/test/lib/custom_test_fail.py"
            },
            { "name": "my-custom-2",
              "description": ["a custom test driver"],
              "target": "https://www.google.com/",
              "driver": "yac/tests/test/lib/custom_test_pass.py"
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        tests.run(Params({}),"",test_names=["my-custom-1","my-custom-2"])

        test_results = tests.get_results()

        # test that the pass count is 1 and passing tests includes
        # the requested test
        self.assertTrue(len(test_results.get_passing_tests()) == 1 )
        self.assertTrue('my-custom-2' in test_results.get_passing_tests())

    def test_custom_fail(self):

        test_descriptor =  {
          "tests": [
            { "name": "my-custom",
              "description": ["a custom test driver"],
              "target": "https://www.google.com/",
              "driver": "yac/tests/test/lib/custom_test_fail.py"
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        tests.run(Params({}),"",test_names=['my-custom'])

        test_results = tests.get_results()

        # test that the failure count is 1
        self.assertTrue(len(test_results.get_failing_tests()) == 1)