import os, json, yaml
from yac.lib.schema import validate
from yac.lib.search import search
from yac.lib.file import get_file_contents
from yac.lib.vaults.vault import Vault

class FileVault(Vault):

    def __init__(self,
                 vault_configs):

        validate(vault_configs, "yac/schema/vaults/file.json")

        self.vault_path = search('"vault-path"', vault_configs)

        # default to json format
        self.format = search("format",vault_configs,"json")

        self.initialized = False
        self.ready = False

    def initialize(self, params):

        err = ""

        if os.path.exists(self.vault_path):
            # pull contents into a dictionary
            file_contents = get_file_contents(self.vault_path)
            self.load(file_contents)
            self.initialized = True
        else:
            err = "vault at %s does not exist"%self.vault_path

        return err

    def load(self, file_contents):

        if self.format == 'json':
            self.vault = json.loads(file_contents)
        elif self.format == 'yaml':
            self.vault = yaml.load(file_contents)

        if self.vault:
            self.ready = True

    def is_ready(self):
        return self.ready

    def is_initialized(self):
        return self.initialized

    def get_type(self):
        return "file"

    def get_format(self):
        return self.format

    def get(self, lookup_str):

        value = search(lookup_str,self.vault)
        return value

    def serialize(self):
        return self.vault

    def update(self, file_contents):

        self.load(file_contents)

        with open(self.vault_path, 'w') as file_arg_fp:
            file_arg_fp.write(file_contents)

    def deserialize(self, serialized_vault):
        # TODO: deprecate

        self.vault = serialized_vault

        with open(self.vault_path, 'w') as file_arg_fp:
            if self.format == "json":
                file_arg_fp.write(json.dumps(self.vault, indent=2))
            elif self.format == "yaml":
                yaml.dump(self.vault, file_arg_fp, default_flow_style=False)

    def __str__(self):
        ret = ("path: %s\n"%self.vault_path +
               "format: %s\n"%self.format +
               "ready: %s\n"%self.ready +
               "data:\n %s\n"%self.vault)
        return ret

def get_vault_filename(service_alias):

    state_filename = "%s-vault.json"%(service_alias)

    return state_filename