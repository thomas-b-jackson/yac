
from pykeepass import PyKeePass
import sys, os
from yac.lib.search import search
from yac.lib.input import string_validation
from yac.lib.cache import get_cache_value, set_cache_value_ms
from yac.lib.schema import validate
from yac.lib.vaults.vault import Vault
from yac.lib.intrinsic import apply_intrinsics

class KeepassVault(Vault):

    def __init__(self,
                 vault_configs):

        validate(vault_configs, "yac/schema/vaults/keepass.json")

        self.vault_path = search('"vault-path"', vault_configs)
        vault_pwd_path = search('"vault-pwd-path"', vault_configs)
        self.vault_pwd = search('"vault-pwd"', vault_configs)

        if not self.vault_pwd and vault_pwd_path and os.path.exists(vault_pwd_path):
            self.vault_pwd = read_pwd_file(vault_pwd_path)

        self.ready = False
        self.initialized = False
        self.kp = None

    def get_type(self):
        return "keepass"

    def initialize(self, params):

        servicefile_path = params.get("servicefile-path","")

        # apply intrinsics in the vault password
        vault_pwd = apply_intrinsics(self.vault_pwd,params)

        full_path = os.path.join(servicefile_path,self.vault_path)

        if os.path.exists(full_path):

            if vault_pwd:
                try:
                    self.kp = PyKeePass(full_path,
                                        password=vault_pwd)
                    self.ready = True
                    self.initialized = True

                except IOError as e:
                    print(e)
            else:
                self.ready = False
                self.initialized = False

    def is_ready(self):
        return self.ready

    def is_initialized(self):
        return self.initialized

    def get(self, lookup_config):

        entry = self.kp.find_entries(path=lookup_config['path'], first=True)

        value = ""

        if entry:
            field_name = lookup_config['field']
            if field_name=="password":
                value = entry.password
            elif field_name=="username":
                value = entry.username
            elif field_name=="url":
                value = entry.url
            elif field_name=="notes":
                value = entry.notes

        return value

    def set(self, lookup_config, secret_value):

        entry = self.kp.find_entries(path=lookup_config['path'], first=True)

        if entry:
            field_name = lookup_config['field']
            if field_name=="password":
                entry.password = secret_value
            elif field_name=="username":
                entry.username = secret_value
            elif field_name=="url":
                entry.url = secret_value

        self.kp.save()

    def load_cached_vault_path(self):

        vault_path = get_cache_value('keepass-vault-path')

        if not vault_path:

            vault_path = string_validation("KeePass Vault Path",
                             "Path to the KeePass vault file for secrets lookup",
                             [],
                             path_validation,
                             True)

            set_cache_value_ms('keepass-vault-path',vault_path)

        return vault_path


    def load_cached_vault_pwd(self):

        vault_pwd = get_cache_value('keepass-vault-pwd')

        if not vault_pwd:

            vault_pwd = string_validation("KeePass Vault Password",
                             "The master key for the KeePass vault",
                             [],
                             string_validation,
                             True,
                             100,
                             True)

            set_cache_value_ms('keepass-vault-pwd', vault_pwd)

        return vault_pwd

    def clear_secrets_cache(self):
        set_cache_value_ms('keepass-vault-path',"")
        set_cache_value_ms('keepass-vault-pwd', "")

def read_pwd_file(vault_pwd_path):

    pwd = ""
    if os.path.exists(vault_pwd_path):
        with open(vault_pwd_path, "r") as pwd_file:
            pwd = pwd_file.read()

    return pwd