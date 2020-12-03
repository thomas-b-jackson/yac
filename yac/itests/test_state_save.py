import unittest, os, random, json
from yac.lib.state import save_state, load_state

class TestCase(unittest.TestCase):


    def test_save_state(self):

        random_value = 'my new random value: %s'%str(random.randint(1, 1000))

        test_state = {
            "key": {
                "comment": "my comment",
                "value": random_value
            }
        }

        service_alias = "test"
        s3_path="dev"

        s3_bucket = save_state(s3_path=s3_path, service_alias=service_alias, state=test_state)

        loaded_state, s3_bucket = load_state(s3_path=s3_path, service_alias=service_alias)

        self.assertTrue(loaded_state and "key" in loaded_state and get_variable(loaded_state,'key') == random_value)
