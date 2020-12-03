import unittest, os, random
from yac.lib.intrinsic import apply_intrinsics, IntrinsicsError
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    # test when a dictionary references a yac-fxn
    def test_yac_fxn(self): 
        
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

        test_dict = {
            "myparam": {
                "comment": "testing",
                "value": {"yac-fxn": "yac/tests/intrinsics/vectors/fxn.py"}
            }
        }

        # run test
        updated_dict = apply_intrinsics(test_dict, Params(params))
        
        # test that the value is populated per the value returned by fxn.py
        fxn_check = updated_dict['myparam']['value'] == "myservice"

        self.assertTrue(fxn_check) 

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

        test_dict = {
            "myparam": {
                "comment": "testing",
                "value": {"yac-fxn": "yac/tests/intrinsics/vectors/nonexistant.py"}
            }
        }

        # run test
        error_received=False
        try:
            updated_dict = apply_intrinsics(test_dict, Params(params))
        except IntrinsicsError as e:
            error_received = True
        
        self.assertTrue(error_received) 
        
    # test when a yac-fxn returns a dict
    def test_dict_yac_fxn(self): 
        
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

        test_dict = {
            "myparam": {
                "comment": "testing",
                "dict": {"yac-fxn": "yac/tests/intrinsics/vectors/dict.py"}
            }
        }

        # run test
        updated_dict = apply_intrinsics(test_dict, Params(params))
        
        # test that the value is populated per the value returned by fxn.py
        fxn_check = updated_dict['myparam']['dict']['key'] == "testvalue"

        self.assertTrue(fxn_check)                                     