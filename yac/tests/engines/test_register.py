import unittest, os, random
from shutil import copyfile

from yac.lib.engines import register_engine

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # copy test vector to tmp location
        cls.configs_path = "/tmp/engines.json"

        copyfile("yac/tests/engines/vectors/engines.json",
        	     cls.configs_path)

    @classmethod
    def tearDownClass(cls):

        # remove test vector from tmp location
        os.remove(TestCase.configs_path)

    def test_load(self):

        err = register_engine(engine_type="stack",
                                  engine_key="gcp",
                                  module_path="yac/tests/engines/vectors/stack.py",
                                  class_name="GCPStack",
                                  configs_path=TestCase.configs_path)

        if err:
        	print(err)
        self.assertTrue(not err)