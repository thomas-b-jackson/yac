import unittest, os
from jsonschema import ValidationError
from yac.lib.vault import SecretVaults

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = [
          {
            "type": "s3",
            "name": "main",
            "configs": {
              "comment": "vault is in our nonprod v2 account",
              "bucket": "gitlab-secrets-dots",
              "vault-path": "gitlab-secrets.json",
              "format": "json"
            }
          },
          {
            "type": "file",
            "name": "local",
            "configs": {
              "comment": "vault is in a local file",
              "vault-path": "/opt/gitlab/etc/secrets.yaml",
              "format": "yaml"
            }
          },
          {
            "type": "keepass",
            "name": "keepass",
            "configs": {
              "comment": "vault is in a local keepass vault",
              "vault-path": "/opt/etc/vault.kdbx",
              "vault-pwd-path": "/tmp/.pwd"
            }
          }
        ]

        # test that no schema validation errors are raised
        validation_success = True
        try:
            secrets = SecretVaults(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")

        self.assertTrue(validation_success==True)

    def test_schema_bad(self):

        # "sources" instead of "source"
        serialized_obj = [
          {
            "type": "s3",
            "names": "main",
            "configs": {
              "comment": "vault is in our nonprod v2 account",
              "bucket": "gitlab-secrets-dots",
              "vault-path": "gitlab-secrets.json",
              "format": "json"
            }
          },
          {
            "type": "file",
            "name": "local",
            "configs": {
              "comment": "vault is in a local file",
              "vault-path": "/opt/gitlab/etc/secrets.yaml",
              "format": "yaml"
            }
          },
          {
            "type": "keepass",
            "name": "keepass",
            "configs": {
              "comment": "vault is in a local keepass vault",
              "vault-path": "/opt/etc/vault.kdbx",
              "vault-pwd-path": "/tmp/.pwd"
            }
          }
        ]

        # test that schema validation errors are raised
        validation_success = True
        try:
            secrets = SecretVaults(serialized_obj)
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)