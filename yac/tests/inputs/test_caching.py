import unittest, os, json
import sys, io
from yac.lib.params import Params
from yac.lib.inputs import Inputs, InputsCacher

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # service name for the purposes of this test
        cls.name = "testing/params-caching"

        # define where we expect inputs to be cached
        cls.cache_rel_path = os.path.join("params.json")

        # define where we expect inputs to be cached
        home = os.path.expanduser("~")

        cls.cache_full_path = os.path.join(home,
                                           ".yac",
                                           cls.name,
                                           cls.cache_rel_path)

    @classmethod
    def tearDownClass(cls):

        # remove any existing cache file
        if os.path.exists(cls.cache_full_path):

            os.remove(cls.cache_full_path)

    def test_params_cache_path(self):

        # remove any existing cache file
        if os.path.exists(TestCase.cache_full_path):
            os.remove(TestCase.cache_full_path)

        test_parameters = {
            "service-name": {
              "value": TestCase.name
            }
        }

        # load params
        params = Params(test_parameters)

        # create an input w/ only one available setpoint
        serialized_inputs_cacher = {
          "enabled": True,
          "path": TestCase.cache_rel_path,
        }

        inputs_cacher = InputsCacher(serialized_inputs_cacher)

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

        inputs = Inputs(serialized_inputs,inputs_cacher)

        # inject the correct response to inputs prompt into stdin
        sys.stdin = io.StringIO('dev')

        # load inputs into params
        inputs.load(params)

        # verify the params file was created
        self.assertTrue(os.path.exists(TestCase.cache_full_path))

        # verify the env params is in the file and set properly
        params_from_file = get_params_from_file(TestCase.cache_full_path)
        self.assertTrue(params_from_file.get('env')=='dev')

    def test_params_empty_cache_path(self):

        # remove any existing cache file
        if os.path.exists(TestCase.cache_full_path):
            os.remove(TestCase.cache_full_path)

        test_parameters = {
            "service-name": {
              "value": TestCase.name
            }
        }

        # load params
        params = Params(test_parameters)

        # create an input w/ only one available setpoint
        serialized_inputs_cacher = {
          "enabled": True
        }

        inputs_cacher = InputsCacher(serialized_inputs_cacher)

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

        inputs = Inputs(serialized_inputs,inputs_cacher)

        # inject the correct response to inputs prompt into stdin
        sys.stdin = io.StringIO('dev')

        # load inputs into params
        inputs.load(params)

        cache_path = inputs_cacher.get_path(params)

        # verify the params file was created
        self.assertTrue(os.path.exists(cache_path))

        # verify the env params is in the file and set properly
        params_from_file = get_params_from_file(cache_path)
        self.assertTrue(params_from_file.get('env')=='dev')

def get_params_from_file(cache_full_path):

  # sneak a peak at file before deleting
  with open(cache_full_path) as file_arg_fp:
      file_contents = file_arg_fp.read()

  return Params(json.loads(file_contents))