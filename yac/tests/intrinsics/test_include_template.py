import unittest, os, random, json
from yac.lib.intrinsic import apply_intrinsics, IntrinsicsError
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    # test including a json file
    def test_include_json(self): 
        
        params = {
          "user-name": {"value": "henry-grantham"}
        }

        test_dict = [{"yac-include": "yac/tests/intrinsics/vectors/include.json"}]

        # run test
        rendered_dict = apply_intrinsics(test_dict,Params(params))

        # updated_dict_str = json.dumps(test_dict)

        ref_check = "henry-grantham" in rendered_dict[0]["key"]

        self.assertTrue(ref_check) 

    # test including a yaml file
    def test_include_yaml(self): 
        
        params = {
          "user-name": {"value": "henry-grantham"}
        }

        test_dict = [{"yac-include": "yac/tests/intrinsics/vectors/include.yaml"}]

        # run test
        rendered_dict = apply_intrinsics(test_dict,Params(params))

        ref_check = "henry-grantham" in rendered_dict[0]["key"]

        self.assertTrue(ref_check)

    # test including a non-existant file
    def test_include_nonexistant(self): 
        
        params = {
          "user-name": {"value": "henry-grantham"}
        }

        test_dict = [{"yac-include": "yac/tests/intrinsics/vectors/include.nonexistant"}]

        # test that an error is raised
        error_raised = False
        try:
            rendered_dict = apply_intrinsics(test_dict,Params(params))
        except IntrinsicsError as e:
            print(e)
            error_raised = True

        self.assertTrue(error_raised)
