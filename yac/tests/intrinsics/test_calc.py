import unittest, os, random
from yac.lib.intrinsic import apply_intrinsics, IntrinsicsError
from yac.lib.params import Params

class TestCase(unittest.TestCase):
 

    def test_no_yac_fxn(self): 
        # test when a dictionary references a non-existant yac-fxn
        
        params = {
            "service-alias" : {
              "type" : "string",
              "value": "myservice"
            },
            "env": {
               "type" : "string",
                "value": "dev"           
            }
        }

        test_dict1 = {
            "myparam": {
                "comment": "testing",
                "value": {"yac-calc": ["yac/tests/intrinsics/vectors/nonexistant.py"]}
            }
        }

        test_dict2 = {
            "myparam": {
                "comment": "testing",
                "value": {"yac-calc": ["no-existant-stock"]}
            }
        }

        # run test
        error_received1=False
        try:
            updated_dict1 = apply_intrinsics(test_dict1, Params(params))
        except IntrinsicsError as e:
            error_received1 = True

        error_received2=False
        try:
            updated_dict2 = apply_intrinsics(test_dict2, Params(params))
        except IntrinsicsError as e:
            error_received2 = True

        self.assertTrue(error_received1)
        self.assertTrue(error_received2)
        
                                    