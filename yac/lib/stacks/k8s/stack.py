# from kubernetes import client, config
import json
from yac.lib.search import search
from yac.lib.inputs import Inputs
from yac.lib.naming import get_stack_name
from yac.lib.stacks.k8s.configmaps import ConfigMaps
from yac.lib.stacks.k8s.secrets import Secrets
from yac.lib.stacks.k8s.services import Services
from yac.lib.stacks.k8s.deployments import Deployments
from yac.lib.stacks.k8s.statefulset import StatefulSets
from yac.lib.stacks.k8s.ingresses import Ingresses
from yac.lib.stacks.k8s.pvcs import PVCs
from yac.lib.stacks.k8s.resource import Resources
from yac.lib.stacks.k8s.builder import get_builder_resources
from yac.lib.params import Params
from yac.lib.input import string_validation
from yac.lib.stacks.stack import Stack
from yac.lib.schema import validate

class K8sStack(Stack):
    # a kubernetes stack

    def __init__(self,
                 serialized_stack):

        """
        Args:
            serialized_stack: A dictionary containing serialized k8s stack,
                              satisfying the yac/schema/stacks/k8s/stack.json schema
        Returns:
            A K8sStack instance

        Raises:
            ValidationError: if a serialized_stack fails schema validation

        """

        # first validate. this should raise an error if
        # required fields aren't present
        validate(serialized_stack, "yac/schema/stacks/k8s/stack.json")

        self.type = "kubernetes"

        self.namespace = search("namespace",serialized_stack,"")

        self.configmaps = ConfigMaps(serialized_stack)

        self.secrets = Secrets(serialized_stack)

        self.deployments = Deployments(serialized_stack)

        self.ingresses = Ingresses(serialized_stack)

        self.statefulsets = StatefulSets(serialized_stack)

        self.services = Services(serialized_stack)

        self.pvcs = PVCs(serialized_stack)

        # generic resources (orchestrated via kubectl)
        self.resources = Resources(serialized_stack)

    def serialize(self):

        return {
            "deployments": self.deployments
        }

    def add(self, stack):

        if (stack.impl and
            stack.impl.type == "kubernetes"):

            self.configmaps.add(stack.impl.configmaps)
            self.secrets.add(stack.impl.secrets)
            self.services.add(stack.impl.services)
            self.ingresses.add(stack.impl.ingresses)
            self.deployments.add(stack.impl.deployments)
            self.statefulsets.add(stack.impl.statefulsets)
            self.pvcs.add(stack.impl.pvcs)
            self.resources.add(stack.impl.resources)

    def build(self,
              params,
              deploy_mode_bool=False,
              context=""):

        err = self.build_all(params,
                       deploy_mode_bool=deploy_mode_bool,
                       dry_run_bool=False,
                       context=context)

        if not err:
            #  build generic resources
            err = self.resources.build(params,
                                       deploy_mode_bool,
                                       context)

        return err

    def dryrun(self,
              params,
              deploy_mode_bool=False,
              context=""):

        err = self.build_all(params,
                       deploy_mode_bool=deploy_mode_bool,
                       dry_run_bool=True,
                       context=context)

        if not err:
            #  dryrun build generic resources
            err = self.resources.dryrun(params,
                                        deploy_mode_bool,
                                        context)
        return err

    def build_all(self,
              params,
              deploy_mode_bool=False,
              dry_run_bool=False,
              context=""):

        self.params = params

        #  build config maps
        err = self.configmaps.build(context,
                                    self.params,
                                    dry_run_bool,
                                    deploy_mode_bool)

        if not err:
            # build secrets
            err = self.secrets.build(context,
                                   self.params,
                                   dry_run_bool,
                                   deploy_mode_bool)
        else:
            return err

        if not err:
            # build pvcs
            err = self.pvcs.build(context,
                                   self.params,
                                   dry_run_bool,
                                   deploy_mode_bool)
        else:
            return err

        if not err:
            # next build deployments
            err = self.deployments.build(context,
                                       self.params,
                                       dry_run_bool,
                                       deploy_mode_bool)
        else:
            return err

        if not err:
            # next build statefulsets
            err = self.statefulsets.build(context,
                                       self.params,
                                       dry_run_bool,
                                       deploy_mode_bool)
        else:
            return err

        if not err:
            # next build services
            err = self.services.build(context,
                                       self.params,
                                       dry_run_bool,
                                       deploy_mode_bool)
        else:
            return err

        if not err:
            # next build ingress (which reference services)
            err = self.ingresses.build(context,
                                       self.params,
                                       dry_run_bool,
                                       deploy_mode_bool)

        else:
            return err

        return err

    def delete(self,
               params,
               context=""):

        self.params = params

        stack_name = get_stack_name(self.params)

        msg = ("The stack deletion requested will delete all k8s resources " +
               "associated with the %s stack.\n"%stack_name +
               "Proceed with deletion? [y,n]>> ")

        if approved(msg):

            #  delete config maps
            err = self.configmaps.delete(context, self.params)

            if not err:
                # delete secrets
                err = self.secrets.delete(context, self.params)
            else:
                return err

            if not err:
                # delete deployments
                err = self.deployments.delete(context, self.params)
            else:
                return err

            if not err:
                # delete pvcs
                err = self.pvcs.delete(context, self.params)
            else:
                return err

            if not err:
                # delete statefulsets
                err = self.statefulsets.delete(context, self.params)
            else:
                return err

            if not err:
                # delete services
                err = self.services.delete(context, self.params)
            else:
                return err

            if not err:
                # delete ingresses
                err = self.ingresses.delete(context, self.params)
            else:
                return err

            if not err:
                # delete generic resources
                err = self.resources.delete(context, self.params)
            else:
                return err

            return err

    def cost( self,
              params,
              context=""):

        # the main cost associated a k8s stack is the per pod cost,
        # which is based on resource requests
        cost_per_month_dollars = self.deployments.cost(params,context)

        print("approximate monthly cost is $%.2f"%cost_per_month_dollars)

    def setup(self,
              params,
              deploy_mode_bool=False,
              context=""):

        # create or update a 'builder' service account that can be
        # used to build this service

        # get all the resource type that are part of this stack
        builder_resources,builder_account_name = get_builder_resources(self, params)

        if builder_resources:

            msg = ("Create or update the builder service account for this service? [y,n]>> ")

            if approved(msg):

                # leverage the Resources class to execute the build
                k8s_resources = Resources({"resources": builder_resources})

                # if not err and approved(msg):
                err = k8s_resources.build(params,
                              deploy_mode_bool,
                              context)

                msg = ("View the builder service account tokens? [y,n]>> ")

                if approved(msg):

                    # get the token associted with the service account
                    token,err = self.get_token(k8s_resources,
                                               builder_account_name,
                                               context)

                    print("token for '%s' service account: %s"%(builder_account_name,
                                                                token))

    def get_token(self,
                  k8s_resources,
                  builder_account_name,
                  context):

        # first get the name of the secret from the 'secrets' attribute
        # of the service account
        kubectl_command = "kubectl --context=%s get sa %s -o json"%(context,builder_account_name)

        print("cmd: %s"%kubectl_command)

        sa_str, err = k8s_resources.run_kubectl(kubectl_command)

        token = ""
        if not err:
            sa_dict = json.loads(sa_str)
            secret_name = search("secrets | [0].name",sa_dict)

            if secret_name:

                token, err = self.secrets.get_secret_value(context,
                                                           secret_name,
                                                           "token")

        return token, err

def approved(msg):

    validation_failed = True
    change = False

    # accept y, n, or empty string
    options = ['y', 'n', '']

    while validation_failed:

        value = input(msg)

        # validate the input
        validation_failed, value = string_validation(value, options, False)

    # approved if 'y' was input
    return value == 'y'