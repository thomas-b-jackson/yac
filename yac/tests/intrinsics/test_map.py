import unittest, os, random, json
from yac.lib.intrinsic import apply_intrinsics, IntrinsicsError
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    # test when a list contains a list
    def test_map(self): 
        
        params = {
            "user-name": {"value": "henry-grantham"},
            "neighborhood-map": {
              "lookup":  "user-name",
              "value": {
                "tom-jackson":    "phinney",
                "henry-grantham": "capital-hill"
              }
            }
        }

        test_dict = {
              "InstancePort": {
                "Ref": "WebServerPort"
              },
              "LoadBalancerName": {"yac-ref": "neighborhood-map"}
        }

        # run test
        updated_dict = apply_intrinsics(test_dict, 
                                        Params(params))

        updated_dict_str = json.dumps(updated_dict)
        
        print(updated_dict_str)

        ref_check = "capital-hill" in updated_dict_str

        self.assertTrue(ref_check) 
      
    # test when a dictionary references a map that doesn't exist
    def test_map_name_error(self): 
        
        params = {
            "user-name": {"value": "henry-grantham"},
            "neighborhood-map": {
              "lookup":  "user-name",
              "value": {
                "tom-jackson":    "phinney",
                "henry-grantham": "capital-hill"
              }
            }
        }

        test_dict = {
              "InstancePort": {
                "Ref": "WebServerPort"
              },
              "LoadBalancerName": {"yac-ref": "neighborhood-maps"}
        }

        # verify we get an error
        error_received=False
        try:
          updated_dict = apply_intrinsics(test_dict, Params(params))
        except IntrinsicsError as e:
          error_received = True

        self.assertTrue(error_received)