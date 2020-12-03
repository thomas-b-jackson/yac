import unittest, os, random
import sys, io
from yac.lib.input import Input
from yac.lib.params import Params


class TestCase(unittest.TestCase):

    def test_optional(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": False,
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject a carriage return
        sys.stdin = io.StringIO("\n")

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that an empty string was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == "")

    def test_optional_w_options(self):

        serialized_input = {
          "key": "color",
          "title": "Color",
          "type": "string",
          "help":  "Your hair color",
          "required": False,
          "options": ["red","brown"]
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject a carriage return
        sys.stdin = io.StringIO("\n")

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that an empty string was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == "")

    def test_required(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject a response
        sys.stdin = io.StringIO("my-stack")

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that 'my-stack' was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == "my-stack")
