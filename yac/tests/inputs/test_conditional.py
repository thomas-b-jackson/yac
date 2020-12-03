import unittest, os, random
import sys, io
from yac.lib.input import Input
from yac.lib.params import Params
 

class TestCase(unittest.TestCase):

    def test_conditional_hit1(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
          "conditions": {
            "kvps": "env:dev"
          }
        }

        inputs = Input(serialized_input)

        params = Params({"env": {"value": "dev"}})

        # inject an invalid response followed by a valid response
        sys.stdin = io.StringIO("my-stack")

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that 'my-stack' was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == 'my-stack')

    def test_conditional_hit2(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
          "conditions": {
            "kvps": "env:dev,date:today"
          }
        }

        inputs = Input(serialized_input)

        params = Params({"env": {"value": "dev"},
                         "date": {"value": "today"}})

        # inject an invalid response followed by a valid response
        sys.stdin = io.StringIO("my-stack")

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that 'my-stack' was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == 'my-stack')

    def test_conditional_miss1(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
          "conditions": {
            "kvps": "env:dev"
          }
        }

        inputs = Input(serialized_input)

        params = Params({"env": {"value": "stage"}})

        # inject an invalid response followed by a valid response
        sys.stdin = io.StringIO("my-stack")

        value, user_prompted = inputs.process(params)

        # test that the user was not prompted and that no value was returned
        self.assertTrue(not user_prompted)
        self.assertTrue(not value)

    def test_conditional_miss2(self):

        serialized_input = {
          "key": "alias",
          "title": "Alias",
          "type": "string",
          "help":  "Name of alias to assign this custom dev stack",
          "required": True,
          "conditions": {
            "kvps": "env:dev,date:today"
          }
        }

        inputs = Input(serialized_input)

        params = Params({"env": {"value": "dev"}})

        # inject an invalid response followed by a valid response
        sys.stdin = io.StringIO("my-stack")

        value, user_prompted = inputs.process(params)

        # test that the user was not prompted and that no value was returned
        self.assertTrue(not user_prompted)
        self.assertTrue(not value)        