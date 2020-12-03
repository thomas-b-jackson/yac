import unittest, os
from yac.lib.vault import SecretVaults

class TestCase(unittest.TestCase):

    def test_source_valid(self):

        secrets_vaults = [
          {
              "type": "s3",
              "name": "s3",
              "configs": {
                "bucket": "gitlab-secure",
                "vault-path": "secrets/s3_vault.json"
              }
             
          }
        ]

        vaults = SecretVaults(secrets_vaults)
        
        # get the resulting s3 vault and assert that it is ready
        vault = vaults.get_vault('s3')

        self.assertTrue(vault.is_ready())  