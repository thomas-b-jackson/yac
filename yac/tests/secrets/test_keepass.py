import unittest, os, random, shutil
from yac.lib.params import Params
from yac.lib.secrets import Secrets
from yac.lib.vault import SecretVaults


class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # write the vault password to the .pwd file
        cls.pwd_path = "/tmp/.pwd"

        # make sure file is not present
        if os.path.exists(cls.pwd_path):
          os.remove(cls.pwd_path)

        # write the pwd to the file
        with open(cls.pwd_path, "w") as text_file:
            text_file.write("open_sesame")

    def test_secrets(self):

        my_secrets = {
            "param-key-1": {
                "comment": "branch 1, child 1, entry 1",
                "source": "keepass",
                "lookup": {
                    "path":  "Branch 1/B1-C1/B1-C1-E1",
                    "field": "password"
                }
            },
            "param-key-2": {
                "comment": "branch 2, child 2, entry 1",
                "source": "keepass",
                "lookup": {
                    "path":  "Branch 2/B2-C2/B2-C2-E1",
                    "field": "password"
                }
            }
        }

        secrets_vaults = [
          {
              "type": "keepass",
              "name": "keepass",
              "configs": {
                "vault-path": "yac/tests/vault/vectors/test_vault.kdbx",
                "vault-pwd-path": TestCase.pwd_path
              }
          }
        ]

        params = Params({})

        vaults = SecretVaults(secrets_vaults)

        secrets = Secrets(my_secrets)

        secrets.load(params,vaults)

        print(secrets.get_errors())

        both_loaded = (params.get("param-key-1")=='b1-c1-e1-secret' and
                       params.get("param-key-2")=='b2-c2-e1-secret')

        self.assertTrue(both_loaded)
