#!/usr/bin/env python

from yac.lib.search import search
from yac.lib.params import Params
from yac.lib.engines import get_credentials_provider

class Credentialers():

    def __init__(self,
                 credentialers_descriptor):

        self.credentialers = {}

        for credentialer_descriptor in credentialers_descriptor:

            name = search('name',credentialer_descriptor,"")
            credentialer_type = search('type',credentialer_descriptor,"")

            self.credentialers[name], err = get_credentials_provider(credentialer_type,
                                                 credentialer_descriptor)

            if err:
                print("credentialer provider for type '%s' not available. err: %s ... exiting"%(credentialer_type,err))
                exit(1)

    def add(self, credentialers):
        # inputs:
        #   credentialers: Credentialers instance

        self.credentialers.update(credentialers.credentialers)

    def create(self,
               name,
               params,
               vaults,
               overwrite_bool):

        err = ""

        if name in list(self.credentialers.keys()):
            err = self.credentialers[name].create(params,
                                                  vaults,
                                                  overwrite_bool)
        else:
            err = ("credentialer '%s' does not exist\n"%name +
                   "available credentialers include: %s"%list(self.credentialers.keys()))

        return err
