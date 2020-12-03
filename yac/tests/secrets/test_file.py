import unittest, os
from yac.lib.vaults.file import FileVault
from yac.lib.vault import SecretVaults

class TestCase(unittest.TestCase):

    def test_file_valid(self):

        file_vault_descriptor = {
            "vault-path": "yac/tests/vault/vectors/file_vault.json",
            "format": "json"
        }

        vault = FileVault(file_vault_descriptor)
        err = vault.initialize({})

        self.assertTrue(vault.is_ready())

    def test_file_contents(self):

        secrets_vaults = [
          {
              "type": "file",
              "name": "my-file",
              "configs": {
                "vault-path": "yac/tests/vault/vectors/file_vault.json",
                "format": "json"
              }

          }
        ]

        vaults = SecretVaults(secrets_vaults)
        vaults.initialize({})

        self.assertTrue(vaults.get("my-file","secret1")=="secret1 value")

        self.assertTrue(vaults.get("my-file","secret2.prod")=="prod value")

        self.assertTrue(vaults.get("my-file","secret3[1]")=="val2")
