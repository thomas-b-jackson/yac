import unittest, os
from jsonschema import ValidationError
from yac.lib.stacks.gcp.stack import GCPStack
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "type": "gcp-cloudmanager",
          "Resources": {}
        }

        # test that no schema validation errors are raised
        stack = GCPStack(serialized_obj)

        err = stack.build(Params({}))

        self.assertTrue(not err)
