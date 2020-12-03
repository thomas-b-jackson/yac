#!/usr/bin/env python
import os, json
from yac.lib.paths import get_root_path
from yac.lib.search import search
from yac.lib.engines import get_stack_provider

# a service stack
class Stack():

    def __init__(self,
                 serialized_stack):

        if serialized_stack:

            stack_type = search('type', serialized_stack, "")

            self.impl,err = get_stack_provider(stack_type, serialized_stack)

            if err:
                print("stack provider for type '%s' not available. err: %s ... exiting"%(stack_type,err))
                exit(1)
        else:
            self.impl = None

    def add(self, stack):

        if self.impl:
            self.impl.add(stack)

    def delete(self, params):

        if self.impl:
            return self.impl.delete(params)

    def build(self,
              params,
              deploy_mode_bool=False,
              dry_run_bool=False,
              context=""):
        # build stack
        #
        # args:
        #   params:           Params instance
        #   deploy_mode_bool: deploy mode?
        #   dry_run_bool:     do dry run build?
        #   context:          string with build context

        err = ""

        if self.impl:

            if not dry_run_bool:

                err = self.impl.build(params,
                                      deploy_mode_bool,
                                      context)
            else:

                # perform any setup needed
                err = self.impl.setup(params,
                                      deploy_mode_bool,
                                      context)

                err = self.impl.dryrun(params,
                                       deploy_mode_bool,
                                       context)

                # if we are in ala-cart mode, encourage user to think about what is changing
                # and to understand the cost implications of the build
                if not err and not deploy_mode_bool:

                    # analyze changes that would occur with this deploy
                    err = self.impl.changes(params,
                                            context)

                    # analyze infrasture costs associated with stack
                    err = self.impl.cost(params,
                                         context)

        else:
            # no implementation, so all builds are successful!
            print("nothing to build")

        return err

    def serialize(self):

        if self.impl:
            return self.impl.serialize()
        else:
            return {}

    def exists(self):

        if self.impl:
            return self.impl.exists()
        else:
            return False

    def __str__(self):

        if self.impl:
            return json.dumps(self.impl.serialize(),indent=2)
        else:
            return {}
