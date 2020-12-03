import unittest, os
from jsonschema import ValidationError
from yac.lib.stacks.k8s.resource import Resources

class TestCase(unittest.TestCase):

    def test_get_pods(self):

        serialized_obj = {}

        stack = Resources(serialized_obj)

        output,err = stack.run_kubectl("kubectl get pods")

        # print(output)

        self.assertTrue(output)

    def test_get_podz(self):

        serialized_obj = {}

        stack = Resources(serialized_obj)

        output,err = stack.run_kubectl("kubectl get podz")

        print(output)

        self.assertTrue(err)