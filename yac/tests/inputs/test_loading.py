import unittest, os, json
import sys, io
from yac.lib.params import Params
from yac.lib.inputs import Inputs

class TestCase(unittest.TestCase):

    def test_params_load(self): 

        # load params
        params = Params({})

        serialized_inputs = [
          {
            "key": "env",
            "title": "Environment",
            "type": "string",
            "help":  "The environment to build stack for",
            "required": True,
            "options": ["dev"]
          }
        ]

        inputs = Inputs(serialized_inputs)

        # inject the correct response to inputs prompt into stdin
        sys.stdin = io.StringIO('dev')

        # load inputs into params
        inputs.load(params)

        self.assertTrue(params.get('env')=='dev')