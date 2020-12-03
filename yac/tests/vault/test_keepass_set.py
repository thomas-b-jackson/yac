import unittest, os, random, string
from shutil import copyfile
from yac.lib.vaults.keepass import KeepassVault


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

        # copy the keepass vault to a tmp location
        cls.vault_path = "/tmp/test_vault.kdbx"

        # make sure vault file is not present
        if os.path.exists(cls.vault_path):
          os.remove(cls.vault_path)

        copyfile("yac/tests/vault/vectors/test_vault.kdbx",
                 cls.vault_path)

    def test_secrets_set(self):

        random_secret = ''.join([random.choice(string.ascii_letters) for n in range(8)]).lower()

        my_secret_lookup = {
            "path":  "Branch 1/B1-C1/B1-C1-F1",
            "field": "password"
        }

        keepass_vault = {
            "vault-path": TestCase.vault_path,
            "vault-pwd": "open_sesame"
        }

        vault = KeepassVault(keepass_vault)
        vault.initialize({})

        err = vault.set(my_secret_lookup,random_secret)

        print(err)
        value = ""
        if not err:
            value = vault.get(my_secret_lookup)

        self.assertTrue(not err)
        self.assertTrue(value == random_secret)

    def test_secrets_get(self):

        my_secret_lookup = {
            "path":  "Branch 1/B1-C1/B1-C1-E1",
            "field": "password"
        }

        keepass_vault = {
            "vault-path": TestCase.vault_path,
            "vault-pwd": "open_sesame"
        }

        vault = KeepassVault(keepass_vault)
        vault.initialize({})

        value = vault.get(my_secret_lookup)

        self.assertTrue(value == "b1-c1-e1-secret")