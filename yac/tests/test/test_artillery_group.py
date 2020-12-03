import unittest, os, random

from yac.lib.test import IntegrationTests

class TestCase(unittest.TestCase):

    def test_test_group(self):

        test_descriptor =  {
          "test-groups": [
            { "name": "read-google",
              "description": ["read from google, twice"],
              "target": "https://www.google.com/",
              "tests": [
                {
                  "name": "read-google-1",
                  "description": ["read from google the first time"],
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
                },
                {
                  "name": "read-google-2",
                  "description": ["read from google a second time"],
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
          ]
        }

        tests = IntegrationTests(test_descriptor)

        group_names = tests.get_group_names()

        # test that the both passed successfully
        self.assertTrue("read-google" in group_names )