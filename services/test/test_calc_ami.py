import unittest, os
from services.lib.calc_runner_ami import do_calc
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_yac_version(self): 
        
        test_parameters = {
            "yac-version" : {
              "value": "2.0"
            }
        }

        ami_id = do_calc([],Params(test_parameters))

        self.assertTrue(ami_id) 