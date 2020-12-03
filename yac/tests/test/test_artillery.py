import unittest
from yac.lib.test import IntegrationTests

class TestCase(unittest.TestCase):

    def test_test(self):

        test_descriptor =  {
          "tests": [
            { "name": "read-google",
              "description": ["read from google"],
              "target": "https://www.google.com/",
              "artillery": {
                "config": "yac/tests/test/vectors/read_google.json",
                "assertions": {
                  "comment": ["assert against aggregated latency stats"],
                  "p95_sec": "10",
                  "median_sec": "7",
                  "error_count": "0",
                  "status": ["200"]
                }
              }
            }
          ]
        }

        tests = IntegrationTests(test_descriptor)

        test_names = tests.get_test_names()

        # test that the test was found
        self.assertTrue("read-google" in test_names)
