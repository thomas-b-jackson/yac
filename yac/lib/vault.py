import os, json, yaml, boto3, botocore
from yac.lib.schema import validate
from yac.lib.search import search
from yac.lib.file import get_file_contents
from yac.lib.engines import get_vault_provider

class SecretVaults():

    def __init__(self,
                 serialized_secret_vaults):

        validate(serialized_secret_vaults, "yac/schema/vaults.json")

        self.vaults = {}

        for vault_descriptor in serialized_secret_vaults:

            vault_key = vault_descriptor['name']
            vault_type = vault_descriptor['type']

            self.vaults[vault_key], err = get_vault_provider(vault_type,
                                                 vault_descriptor['configs'])

            if err:
                print("vault provider for type '%s' not available. err: %s ... exiting"%(vault_type,err))
                exit(1)

    def initialize(self, params):

        for vault_key in list(self.vaults.keys()):

            # initialize the vault
            self.vaults[vault_key].initialize(params)

    def get(self, vault_key, secret_search):

        secret_value = ""
        if vault_key in list(self.vaults.keys()):

            if self.vaults[vault_key].is_ready():
                secret_value = self.vaults[vault_key].get(secret_search)

        return secret_value

    def add(self,vault):

        if vault.vaults:
            self.vaults.update(vault.vaults)

    def set_vault(self, vault_key, vault):
        self.vaults[vault_key] = vault

    def get_vaults(self):
        return self.vaults

    def get_vault(self, vault_key):
        if vault_key in self.vaults:
            return self.vaults[vault_key]
        else:
            return None

    def __str__(self):

        if self.vaults:
            ret = ""
            for vault_key in list(self.vaults.keys()):

                ret = ret + "%s:\n %s\n"%(vault_key,str(self.vaults[vault_key]))
        else:
            ret = "none"

        return ret