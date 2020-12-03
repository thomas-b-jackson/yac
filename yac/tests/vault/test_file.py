import unittest, os
from yac.lib.vault import SecretVaults
from yac.lib.vaults.file import FileVault

class TestCase(unittest.TestCase):

    def test_json_file_valid(self):

        secrets_vault = {
            "vault-path": "yac/tests/vault/vectors/file_vault.json"
        }

        vault = FileVault(secrets_vault)
        vault.initialize({})

        self.assertTrue(vault.is_ready())

    def test_yaml_file_valid(self):

        secrets_vault = {
            "vault-path": "yac/tests/vault/vectors/file_vault.yaml",
            "format": "yaml"
        }

        vault = FileVault(secrets_vault)
        vault.initialize({})

        self.assertTrue(vault.is_ready())

    def test_json_file_source(self):

        secrets_vaults = [
          {
              "type": "file",
              "name": "file-1",
              "configs": {
                "vault-path": "yac/tests/vault/vectors/file_vault.json"
              }

          }
        ]

        vaults = SecretVaults(secrets_vaults)
        vaults.initialize({})
        # get the results keepass vault and assert that it is available
        vault = vaults.get_vault('file-1')

        self.assertTrue(vault)