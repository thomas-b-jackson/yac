import unittest, os
from yac.lib.vaults.keepass import KeepassVault

class TestCase(unittest.TestCase):

    def test_source_valid(self):

        # write the vault password to the .pwd file
        pwd_path = "/tmp/.pwd"

        # make sure file is not present
        if os.path.exists(pwd_path):
          os.remove(pwd_path)

        # write the pwd to the file
        with open(pwd_path, "w") as text_file:
            text_file.write("open_sesame")

        keepass_vault = {
                "vault-path": "yac/tests/vault/vectors/test_vault.kdbx",
                "vault-pwd-path":   pwd_path
              }

        vault = KeepassVault(keepass_vault)

        vault.initialize({})

        self.assertTrue(vault.is_ready())
