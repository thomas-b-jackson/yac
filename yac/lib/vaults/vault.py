class Vault():
    # base class for all yac vaults

    def initialize(self, params):
        err = ""
        return err

    def is_initialized(self):
        return True

    def get_type(self):
        return ""

    def get(self, lookup_str):
        return ""

    def set(self, lookup_str, value):
        err = ""
        return err