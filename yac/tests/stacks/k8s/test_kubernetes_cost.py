import unittest, os, random
from yac.lib.stacks.k8s.stack import K8sStack
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_stack(self):

        serialized_stack = {
            "type": "kubernetes",
            "deployments": [
              {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "spec": {
                  "replicas": 2,
                  "template": {
                    "spec": {
                      "resources": {
                        "requests": {
                          "memory": "129M",
                          "cpu": 3
                        },
                        "limits": {
                          "memory": "250M",
                          "cpu": 4
                        }
                      }
                    }
                  }
                }
              }
            ]
          }

        stack = K8sStack(serialized_stack)

        stack.cost(Params({}))

        self.assertTrue(stack)
