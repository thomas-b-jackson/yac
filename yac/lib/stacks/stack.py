class Stack():
    # base class for all yac stacks

    def __init__(self,
                 serialized_stack):
        # args:
        #    serialized_stack: dict containing the stack object from the Stack stanza
        #                      in the Servicefile

        # use the yac.lib.schema module to validate the serialized_stack, e.g.:
        # validate(serialized_stack, "yac/schema/stacks/my_stack_type.json")

        # use the yac.lib.search module to grab fields from the serialized_stack, e.g.:
        # self.name = search('name', serialized_stack)

        print("init complete")

    def add(self, stack):
        #
        # merge in resources from another stack of this type
        #
        # args:
        #  stack: an instance of this stack class

        print("thanks, but no resources defined so nothing to add")

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

        print("nothing to build")

    def dryrun(self,
              params,
              deploy_mode_bool,
              context=""):
        #
        # do a dry-run build of the infrastructure needed by service
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)
        #   context: the 'build-conext' string from the pipeline

        print("dry run builds not supported")

    def setup(self,
              params,
              deploy_mode_bool,
              context=""):
        #
        # setup permissions needed for running this stack in a pipeline
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)
        #   context: the 'build-conext' string from the pipeline

        print("setup not supported")


    def delete(self,
               params,
               context=""):
        #
        # delete the infrastructure used by service
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)
        #   context: the 'build-conext' string from the pipeline

        print("deletion not supported")

    def cost( self,
              params,
              context=""):
        #
        # provide an estimate of the infrastructure costs associated with the stack
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)

      	print("costing not supported")

    def changes( self,
                 params,
                 context=""):
        #
        # provide an overview of the changes associated with the stack update
        # args:
        #   params: a Params instance, containing all params (including inputs and secrets)

        print("change analysis not supported")