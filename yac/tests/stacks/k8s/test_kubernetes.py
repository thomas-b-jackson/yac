import unittest, os, random
from yac.lib.stacks.k8s.stack import K8sStack
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_stack(self):

        serialized_stack = {
            "type": "kubernetes",
            "configmaps": [
              {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                  "name": "google-monitor",
                  "labels": {
                    "app": "artifactory"
                  }
                },
                "data": {
                  "monitorconfigs.json": "{\n   \"gitlab_latency\": {\n   \"url\": \"https://www.google.com\",\n   \"description\": [\"Measure Gitlab latency via the login page and post via the 'gitlab_login' metric.\",\n           \"Include the HTTP status code with each measurement and post via the 'gitlab_login_status_code' metric\"],\n   \"latency-metric\": \"google_search\",\n   \"period-mins\": \"1\",\n   \"status-metric\": \"google_search_status_code\"\n   }\n }"
                }
              }
            ]
          }

        stack = K8sStack(serialized_stack)

        self.assertTrue(stack)
