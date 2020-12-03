#!/usr/bin/env python

import copy, json
from yac.lib.search import search
from yac.lib.schema import validate
from yac.lib.intrinsic import apply_intrinsics

class Secrets():

    def __init__(self,
                 serialized_secrets):

        # validate. this will raise a validation error if
        # required fields aren't present
        validate(serialized_secrets, "yac/schema/secrets.json")

        self.values = serialized_secrets
        self.errors = []

    def set_vaults(self, vaults):
        self.vaults = vaults

    def add(self, secrets):

        self.values.update(secrets.values)

    def load(self, params, vaults=None):

        if vaults:
            self.vaults = vaults

        # initialize vaults
        vaults.initialize(params)

        # load secrets into the params object passed in
        rendered_values = apply_intrinsics(self.values,params)

        # the secret key is also the param key
        for param_key in list(rendered_values.keys()):

            secret_value = self.vaults.get(rendered_values[param_key]['source'],
                                           rendered_values[param_key]['lookup'])

            if secret_value:
                comment = rendered_values[param_key]['comment']

                # load secret into a param
                params.set(param_key,
                           secret_value,
                           comment)
            else:
                # lookup failed
                msg =( "secret for '%s' at path '%s' "%(param_key,
                                                        rendered_values[param_key]['lookup']) +
                       "does not exist in the '%s' vault"%rendered_values[param_key]['source'] )

                self.load_failure(msg)


    def load_failure(self, failure_msg):

        # add msg to list of errors
        self.errors = self.errors +[failure_msg]

    def get_errors(self):
        return self.errors

    def clear_errors(self):
        self.errors = []

    def __str__(self):
        return json.dumps(self.values,indent=2)
