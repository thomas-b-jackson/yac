import unittest, os
from yac.lib.vaults.b64 import B64Vault
from yac.lib.vault import SecretVaults

class TestCase(unittest.TestCase):

    def test_file_valid(self):

        file_vault_descriptor = {
          "vault-path": "yac/tests/vault/vectors/b64_vault.yaml"
        }

        vault = B64Vault(file_vault_descriptor)
        err = vault.initialize({})

        self.assertTrue(vault.is_ready())

    def test_file_contents(self):

        secrets_vaults = [
          {
              "type": "b64",
              "name": "my-file",
              "configs": {
                  "vault-path": "yac/tests/vault/vectors/b64_vault.yaml"
              }

          }
        ]

        vaults = SecretVaults(secrets_vaults)
        vaults.initialize({})

        self.assertTrue(vaults.get("my-file","secret1")=="secret1 value")

        self.assertTrue(vaults.get("my-file","secret2.prod")=="prod value")

        self.assertTrue(vaults.get("my-file","secret3[1]")=="val2")
