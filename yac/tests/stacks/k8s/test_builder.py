import unittest, os, random, json
from yac.lib.stacks.k8s.builder import get_recommended_rules,load_yaml
from yac.lib.stacks.k8s.stack import K8sStack

class TestCase(unittest.TestCase):

    def test_rules_no_resources(self):

        serialized_obj = {
          "type": "kubernetes",
          "configmaps": [],
          "secrets": [],
          "pvcs": [],
          "ingresses": [],
          "deployments": [],
          "statefulsets": [],
          "services": []
        }

        k8s_stack = K8sStack(serialized_obj)
        rules = get_recommended_rules(k8s_stack)
        self.assertTrue(len(rules)==0)

    def test_rules_secrets(self):

        serialized_obj = {
          "type": "kubernetes",
          "configmaps": [],
          "secrets": [{}],
          "pvcs": [],
          "ingresses": [],
          "deployments": [],
          "statefulsets": [],
          "services": []
        }

        k8s_stack = K8sStack(serialized_obj)
        rules = get_recommended_rules(k8s_stack)
        self.assertTrue(len(rules)==1)

    def test_rules_deployments(self):

        serialized_obj = {
          "type": "kubernetes",
          "configmaps": [],
          "secrets": [],
          "pvcs": [],
          "ingresses": [],
          "deployments": [{}],
          "statefulsets": [],
          "services": []
        }

        k8s_stack = K8sStack(serialized_obj)
        rules = get_recommended_rules(k8s_stack)
        # should get rules for pods and deployments
        self.assertTrue(len(rules)==2)

    def test_load_yaml(self):

        docs = load_yaml()

        self.assertTrue(len(docs)==3)