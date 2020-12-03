import unittest
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_map(self):

        test_parameters = {
            "user-name": {
              "value": "tom-johnson"
            },
            "neighborhood-map": {
              "lookup":  "user-name",
              "value": {
                "tom-johnson":    "phinney",
                "henry-grantham": "queen-ann-hill"
              }
            }
        }

        params = Params(test_parameters)

        self.assertTrue(params.get("neighborhood-map") == "phinney")

    def test_map_miss(self):

        # user-name doesn't match any of the map keys

        test_parameters = {
            "user-name": {
              "value": "tom-johnsons"
            },
            "neighborhood-map": {
              "lookup":  "user-name",
              "value": {
                "tom-johnson":    "phinney",
                "henry-grantham": "queen-ann-hill"
              }
            }
        }

        params = Params(test_parameters)

        value = params.get("neighborhood-map","m.i.a")

        self.assertTrue(value == "m.i.a")
