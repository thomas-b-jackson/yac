import unittest, os, random, json
from yac.lib.intrinsic import apply_intrinsics, IntrinsicsError
from yac.lib.params import Params


class TestCase(unittest.TestCase):

    def test_join(self):

        params = {
            "image-name" : {
              "type" : "string",
              "value": "godzilla"
            },
            "image-label": {
               "type" : "boolean",
                "value": "1.0"
            }
        }

        test_dict = {
          "yac-join": [":",[{"yac-join": ["",
                 ["gitlab-registry.nordstrom.com/",
                  {"yac-ref":"image-name"}]]},
                  {"yac-ref":"image-label"}]]}

        # run test
        updated_dict = apply_intrinsics(test_dict, Params(params))

        updated_dict_str = json.dumps(updated_dict)

        print(updated_dict_str)

        ref_check = "godzilla" in updated_dict_str

        self.assertTrue(ref_check)