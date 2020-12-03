import unittest
from yac.lib.params import Params
from yac.lib.test import IntegrationTests

class TestCase(unittest.TestCase):

    # test a group
    def test_group(self):

        test_descriptor =  {
          "test-groups": [
            {
              "name": "group-1",
              "target": "https://www.google.com/",
              "tests": [
                { "name": "my-custom-1",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                },
                { "name": "my-custom-2",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                }
              ]
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        tests.run(Params({}),context="",group_names=["group-1"])

        test_results = tests.get_results()

        # test that all pass
        self.assertTrue( len(test_results.get_passing_tests()) == 2 )

    # test a specific group can be selected
    def test_group_select(self): 

        test_descriptor =  {
          "test-groups": [
            {
              "name": "group-1",
              "target": "https://www.google.com/",
              "tests": [
                { "name": "my-custom-1",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                },
                { "name": "my-custom-2",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                }
              ]
            },
            {
              "name": "group-2",
              "target": "https://www.google.com/",
              "tests": [
                { "name": "my-custom-3",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                },
                { "name": "my-custom-4",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                }
              ]
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        tests.run(Params({}),context="",group_names=["group-2"])

        test_results = tests.get_results()

        # test that the pass count is 2 and passing tests includes
        # the requested test
        self.assertTrue( len(test_results.get_passing_tests()) == 2 ) 
        self.assertTrue('my-custom-3' in test_results.get_passing_tests())
        self.assertTrue('my-custom-4' in test_results.get_passing_tests())

    # test a specific test within a group can be selected
    def test_group_test_select(self): 

        test_descriptor =  {
          "test-groups": [
            {
              "name": "group-1",
              "target": "https://www.google.com/",
              "tests": [
                { "name": "my-custom-1",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                },
                { "name": "my-custom-2",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                }
              ]
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        tests.run(Params({}),context="",group_names=["group-1:my-custom-2"])

        test_results = tests.get_results()

        # test that the pass count is 1 and passing tests includes
        # the requested test
        self.assertTrue( len(test_results.get_passing_tests()) == 1 ) 
        self.assertTrue('my-custom-2' in test_results.get_passing_tests())

    # test a specifing a non-existent test within a group errors out
    # correctly
    def test_group_test_misselect(self): 

        test_descriptor =  {
          "test-groups": [
            {
              "name": "group-1",
              "target": "https://www.google.com/",
              "tests": [
                { "name": "my-custom-1",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                },
                { "name": "my-custom-2",
                  "description": ["a custom test driver"],
                  "target": "https://www.google.com/",
                  "driver": "yac/tests/test/lib/custom_test_pass.py"
                }
              ]
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        err = tests.run(Params({}),context="",group_names=["group-1:my-custom-na"])

        test_results = tests.get_results()

        # test that the pass count is 0 and that an error was returned
        self.assertTrue( len(test_results.get_passing_tests()) == 0 )
        print(err)
        self.assertTrue(err)
