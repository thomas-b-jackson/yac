import os, json, yaml, base64
from yac.lib.schema import validate
from yac.lib.search import search
from yac.lib.file import load_dict_from_file
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.vaults.vault import Vault

class B64Vault(Vault):

    def __init__(self,
                 vault_configs):

        validate(vault_configs, "yac/schema/vaults/b64.json")

        self.vault_path = search('"vault-path"', vault_configs)
        self.vault_pwd = search('"vault-pwd"', vault_configs)

        # default to json format
        self.format = search("format",vault_configs,"json")

        self.initialized = False
        self.ready = False

    def initialize(self, params):

        err = ""

        servicefile_path = params.get("servicefile-path","")

        # apply intrinsics in the vault password
        vault_pwd = apply_intrinsics(self.vault_pwd,params)

        self.vault,err = load_dict_from_file(self.vault_path, servicefile_path)

        if not err:
            self.initialized = True
            self.ready = True
        else:
            err = "vault at %s does not exist"%self.vault_path
            print(err)

        return err

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
        return base64.b64decode(value).strip().decode("utf-8")

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