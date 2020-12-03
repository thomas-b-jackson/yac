class GCPStack():

    # demo of how one might add support for a new cloud provider (gcp in this case)

    def __init__(self,
                 serialized_stack):

      print("loaded")

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