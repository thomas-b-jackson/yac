from yac.lib.stacks.stack import Stack
from yac.lib.search import search
from yac.lib.schema import validate


class GCPStack(Stack):

    # demo of how one might add support for a new cloud provider (gcp in this case)

    def __init__(self,
                 serialized_stack):
        # args:
        #    serialized_stack: dict containing the stack object from the Stack stanza
        #                      in the Servicefile

        # use the yac.lib.schema module to validate the serialized_stack, e.g.:
        validate(serialized_stack, "yac/schema/stacks/gcp/stack.json")

        # use the yac.lib.search module to grab fields from the serialized_stack, e.g.:
        self.name = search('name', serialized_stack)
        self.resources = search("Resources",serialized_stack, {})
        self.conditions = search("Conditions",serialized_stack, {})

    def add(self, stack):
        #
        # merge in resources from another stack of this type
        #
        # args:
        #  stack: an instance of this stack class

        if (stack.impl and
            stack.impl.type == "gcp-cloudmanager"):

            self.resources.update(stack.impl.resources)
            self.conditions.update(stack.impl.conditions)

    def build(self,
              params,
              deploy_mode_bool=False,
              context=""):
        #
        # build the infrastructure needed by service
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)
        #   deploy_mode_bool: set to true if in pipeline mode (vs ala carte mode)
        #   context: the 'build-conext' string from the pipeline

        print("build your gcp stack (whirring noises ...)")

    def dryrun(self,
              params,
              deploy_mode_bool,
              context=""):
        #
        # do a dry-run build of the infrastructure needed by service
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)
        #   deploy_mode_bool: set to true if in pipeline mode (vs ala carte mode)
        #   context: the 'build-conext' string from the pipeline

        print("dryrun build of your gcp stack ... not!")

    def delete(self,
               params,
               context=""):
        #
        # delete the infrastructure used by service
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)
        #   context: the 'build-conext' string from the pipeline

        print("deletion must be done via cloud manager ui. sorry!")

    def cost( self,
              params,
              context=""):
        #
        # provide an estimate of the infrastructure costs associated with the stack
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)

        print("costing not supported. need to do some digging to see if this is supported ...")

    def setup( self,
              params,
              deploy_mode_bool,
              context=""):
        #
        # performs any setup needed (typically the creation of service accounts needed by pipelines)

        print("setup not supported. check back soon!")