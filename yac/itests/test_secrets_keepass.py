import unittest, os, random, shutil
from yac.lib.keepass import KeepassLoader

class TestCase(unittest.TestCase):

    # test that the loader will detect the lack of vault params in
    # its contructor and prompt for the params
    def test_secrets(self):

        vault_path = "yac/tests/test_vectors/keepass/test_vault.kdbx"
        vault_pwd = "open_sesame"

        print("when prompoted, enter the following params\n")
        print("vault_path: %s\n"%vault_path)
        print("vault_pwd: %s\n"%vault_pwd)

        loader = KeepassLoader()

        load_success = loader.is_ready()
        loader.clear_secrets_cache()

        self.assertTrue(load_success)
