#!/usr/bin/env python
import json, time
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException
from pprint import pprint
from yac.lib.search import search
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.stacks.k8s.resource import Resources
from yac.lib.stacks.k8s.credentials import load_context, get_current_namespace

class Ingresses(Resources):
    # a bunch of kubernetes ingress resources

    def __init__(self,
                 serialized_kubernetes_stack):

        self.resource_array = search("ingresses",serialized_kubernetes_stack,[])

    def build(self,
              context,
              params,
              dry_run_bool,
              deploy_mode_bool):

        self.params = params

        # load context
        err = load_context(context)

        # do not proceed if context could not be loaded
        if err:
            return err

        # get the namespace from the current context
        self.namespace, err = get_current_namespace()

        # do not proceed if namespace not found
        if err:
            return err

        self.api = self.get_extensions_api()

        # render intrinsics in ingresss
        rendered_ingresses = apply_intrinsics(self.resource_array, params)

        err = ""
        if dry_run_bool:
            return self.build_dryrun(rendered_ingresses,
                                     deploy_mode_bool)

        for ingress in rendered_ingresses:

            ingress_name = ingress['metadata']['name']

            ingress_exists,err = self.ingress_exists(ingress_name)

            if not ingress_exists and not err:

                # ingress does not yet exist
                # create it from scratch
                try:
                    api_response = self.api.create_namespaced_ingress(self.namespace,
                                                                         ingress)

                    print("ingress '%s' created"%ingress_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break

            elif ingress_exists and not err:

                # ingress exists, so update it
                try:
                    api_response = self.api.replace_namespaced_ingress(ingress_name,
                                                                          self.namespace,
                                                                          ingress)

                    print("ingress '%s' updated"%ingress_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break
            else:
                err = "Exception when attempting to inspect the ingress %s:\n %s"%(ingress_name,err)
                break

            # if we are error free AND this build is happening in the context of a
            # deploy, wait for pods to pass readiness
            if not err and deploy_mode_bool:
                self.wait(ingress_name)

        return err

    def wait(self, ingress_name):

        # ingress creation should be instantaneous
        print("ingresses assumed ready ...")

    def build_dryrun(self, ingresss_array, deploy_mode_bool):

        err = ""

        # print json.dumps(ingresss_array,indent=2)

        for ingress in ingresss_array:

            ingress_name = ingress['metadata']['name']

            ingress_exists,err = self.ingress_exists(ingress_name)

            if not ingress_exists and not err:
                print("ingress '%s' will be created as it does not yet exist"%ingress_name)
            elif ingress_exists and not err:
                print("ingress '%s' will be updated"%ingress_name)
            else:
                err = "Exception when attempting to inspect the %s ingress: %s\n"%(ingress_name,err)
                break

        if not err:

            self.show_rendered_templates(ingresss_array,
                                         'ingress',
                                         deploy_mode_bool)

        return err

    def ingress_exists(self,ingress_name):

        err = ""
        exists = False

        try:
            api_response = self.api.read_namespaced_ingress(ingress_name,
                                                               self.namespace)
            # if the ingress is found, no ApiException will be raised
            exists = True

        except ApiException as e:

            # the "Not Found" reason is the expected response if the ingress
            # does not exists. any other reason constitutes an error
            if e.reason != "Not Found":
                err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))

        return exists, err

    def delete(self, context, params):

        err = ""

        # load context
        err = load_context(context)

        # do not proceed if context could not be loaded
        if err:
            return err

        # get the namespace from the current context
        self.namespace, err = get_current_namespace()

        # do not proceed if namespace not found
        if err:
            return err

        self.api = self.get_extensions_api()

        # render intrinsics in ingresss
        rendered_ingresses = apply_intrinsics(self.resource_array, params)

        for ingress in rendered_ingresses:

            ingress_name = ingress['metadata']['name']

            _ingress_exists,err = self.ingress_exists(ingress_name)

            if _ingress_exists and not err:

                try:
                    body = kubernetes.client.V1DeleteOptions()
                    print("deleting ingress: %s in namespace: %s"%(ingress_name,self.namespace))
                    api_response = self.api.delete_namespaced_ingress(ingress_name,
                                                                     self.namespace,
                                                                     body,
                                                                     propagation_policy='Orphan')

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
        return err