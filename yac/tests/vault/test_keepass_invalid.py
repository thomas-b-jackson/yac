import unittest, os
from yac.lib.vault import SecretVaults
from jsonschema import ValidationError
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

        secrets_vaults = [
          {
              "type": "keepass",
              "name": "keepass-1",
              "configs": {
                "vault-path": "yac/tests/vaults/vectors/test_vault.kdbx",
                "vault-pwd-path":   pwd_path
              }

          }
        ]

        vaults = SecretVaults(secrets_vaults)

        # get the results keepass vault and assert that it is available
        vault = vaults.get_vault('keepass-1')

        self.assertTrue(vault)

    def test_source_invalid(self):

        # vault-pwd is an invalid config setting for keepass
        secrets_vaults = [
          {
              "type": "keepass",
              "name": "keepass-1",
              "configs": {
                "vault-path": "yac/tests/vaults/vectors/test_vault.kdbx",
                "vault-pwd":   "/path/does/not/matter/for/this/test"
              }

          }
        ]

        # test that these invalid vault configs don't throw a validation error
        vaults = SecretVaults(secrets_vaults)

        self.assertTrue(vaults)

    def test_bad_master_key(self):

        # right vault, wrong password
        vault_config = {
                "vault-path": "yac/tests/vaults/vectors/test_vault.kdbx",
                "vault-pwd-path": "yac/never_gonna_happen.kdbx"
              }

        vault = KeepassVault(vault_config)
        vault.initialize({})

        self.assertTrue(vault.is_ready()==False)

    def test_bad_vault_path(self):

        # non-existent pwd file
        vault_config = {
                "vault-path": "yac/tests/vaults/vectors/test_vault.kdbx",
                "vault-pwd-path": "yac/never_gonna_happen.kdbx"
              }

        vault = KeepassVault(vault_config)
        vault.initialize({})

        self.assertTrue(vault.is_ready()==False)
