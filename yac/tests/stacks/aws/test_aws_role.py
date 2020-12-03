import unittest, os, random, shutil
from yac.lib.stacks.aws.credentials import create_role_config
from yac.lib.stacks.aws.paths import get_configs_path

class TestCase(unittest.TestCase):

    def test_assume_role(self):

        configs_file_path = get_configs_path()

        if os.path.exists(configs_file_path):
            os.remove(configs_file_path)

        create_role_config("test-arn")

        self.assertTrue(os.path.exists(configs_file_path))