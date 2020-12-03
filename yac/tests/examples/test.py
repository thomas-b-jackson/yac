import unittest, os, random
from yac.lib.examples import get_all_keys
from yac.lib.service import get_service

class TestCase(unittest.TestCase):

    def test_get_keys(self):

        keys = get_all_keys()

        print(keys)
        self.assertTrue(keys)

    def test_load_service(self):

        keys = get_all_keys()

        for key in keys:
            # make sure all but the "engines" examples load
            if "engines" not in key:
                ex_path = os.path.join("examples",key)
                service, err = get_service(ex_path)
                self.assertTrue(not err)