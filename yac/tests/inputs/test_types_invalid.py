import unittest, os, random
import sys, io
from yac.lib.input import Input
from yac.lib.params import Params
 

class TestCase(unittest.TestCase):

    def test_string_invalid_option(self):

        serialized_input = {
          "key": "env",
          "title": "Environment",
          "type": "string",
          "help":  "The environment to build stack for",
          "required": True,
          "options": ["stage"]
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject an invalid response followed by a valid response
        sys.stdin = io.StringIO("dev\nstage")

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that dev was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == 'stage')

    def test_int_invalid(self):

        serialized_input = {
          "key": "scale",
          "type": "int",
          "title": "Scale",
          "help":  "Horizontal scale",
          "required": True
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject an invalid response followed by a valid response
        sys.stdin = io.StringIO("test\n13")

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that dev was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == 13)

    def test_bool_invalid(self):

        serialized_input = {
          "key": "rebuild",
          "title": "Rebuilt",
          "type": "bool",
          "help":  "Rebuild the stack?",
          "required": True
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject an invalid response followed by a valid response
        sys.stdin = io.StringIO('yes\nfalse')

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that dev was returned
        self.assertTrue(user_prompted)
        self.assertTrue(not value)  
