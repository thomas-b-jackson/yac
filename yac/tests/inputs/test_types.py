import unittest, os, random
import sys, io
from yac.lib.input import Input
from yac.lib.params import Params


class TestCase(unittest.TestCase):

    def test_string_no_options(self):

        serialized_input = {
          "key": "env",
          "title": "Environment",
          "type": "string",
          "help":  "The environment to build stack for",
          "required": True
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject the correct response to inputs prompt into stdin
        sys.stdin = io.StringIO('dev')

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that dev was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == 'dev')

    def test_string_options(self):

        serialized_input = {
          "key": "env",
          "title": "Environment",
          "type": "string",
          "help":  "The environment to build stack for",
          "required": True,
          "options": ["dev","stage","prod"]
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject the correct response to inputs prompt into stdin
        sys.stdin = io.StringIO('dev')

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that dev was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == 'dev')

    def test_int(self):

        serialized_input = {
          "key": "scale",
          "type": "int",
          "title": "Scale",
          "help":  "Horizontal scale",
          "required": True
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject the correct response to inputs prompt into stdin
        sys.stdin = io.StringIO('4')

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that dev was returned
        self.assertTrue(user_prompted)
        self.assertTrue(value == 4)

    def test_bool(self):

        serialized_input = {
          "key": "rebuild",
          "title": "Rebuilt",
          "type": "bool",
          "help":  "Rebuild the stack?",
          "required": True
        }

        inputs = Input(serialized_input)

        params = Params({})

        # inject the correct response to inputs prompt into stdin
        sys.stdin = io.StringIO('False')

        value, user_prompted = inputs.process(params)

        # test that the user was prompted and that dev was returned
        self.assertTrue(user_prompted)
        self.assertTrue(not value)

    # TODO: 2to3 fix (failing)
    # def test_path(self):

    #     serialized_input = {
    #       "key": "syslog",
    #       "title": "System Log Path",
    #       "type": "path",
    #       "help":  "Path to syslog file",
    #       "required": True
    #     }

    #     inputs = Input(serialized_input)

    #     params = Params({})

    #     # inject the correct response to inputs prompt into stdin
    #     sys.stdin = io.StringIO('/var/log/system.log')

    #     value, user_prompted = inputs.process(params)

    #     # test that the user was prompted and that dev was returned
    #     self.assertTrue(user_prompted)
    #     self.assertTrue(value == '/var/log/system.log')