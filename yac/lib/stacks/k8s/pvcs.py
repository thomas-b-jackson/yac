#!/usr/bin/env python
import json

import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException
from pprint import pprint
from yac.lib.search import search
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.stacks.k8s.resource import Resources
from yac.lib.template import apply_stemplate, TemplateError
from yac.lib.stacks.k8s.credentials import load_context, get_current_namespace

class PVCs(Resources):
    # a bunch of kubernetes persistent volume claims

    def __init__(self,
                 serialized_kubernetes_stack):

        self.resource_array = search("pvcs",serialized_kubernetes_stack,[])

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

        self.api = self.get_core_api()

        # render intrinsics in pvcs
        rendered_pvcs = apply_intrinsics(self.resource_array, params)

        err = ""
        if dry_run_bool:
            return self._build_dryrun(rendered_pvcs,
                                      deploy_mode_bool)

        for pvc in rendered_pvcs:

            pvc_name = pvc['metadata']['name']

            _pvc_exists,err = self._pvc_exists(pvc_name)

            if not _pvc_exists and not err:

                # pvc does not yet exist
                # create it from scratch
                try:
                    api_response = self.api.create_namespaced_persistent_volume_claim(self.namespace,
                                                                                      pvc)

                    print("pvc '%s' created"%pvc_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break

            elif _pvc_exists and not err:

                # pvs exists, and pvcs are immutable.
                print("pvc '%s' already exists. pvcs are immutable, "%pvc_name)
                print(" so if you want it replaced, delete it manually then re-build the stack")

            else:
                err = "Exception when attempting to inspect the pvc %s:\n %s"%(pvc_name,err)
                break

        return err

    def _build_dryrun(self, pvc_array, deploy_mode_bool):

        err = ""

        for pvc in pvc_array:

            pvc_name = pvc['metadata']['name']

            _pvc_exists,err = self._pvc_exists(pvc_name)

            if not _pvc_exists and not err:
                print("pvc '%s' will be created as it does not yet exist"%pvc_name)
            elif _pvc_exists and not err:
                print("pvc '%s' will be updated"%pvc_name)
            else:
                err = "Exception when attempting to inspect the %s config_pvc: %s\n"%(pvc_name,err)
                break

        if not err:

            self.show_rendered_templates(pvc_array,
                                         'pvc',
                                         deploy_mode_bool)

        return err

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

        self.api = self.get_core_api()

        # render intrinsics in pvcs
        rendered_pvcs = apply_intrinsics(self.resource_array, params)

        for pvc in rendered_pvcs:

            pvc_name = pvc['metadata']['name']

            _pvc_exists,err = self._pvc_exists(pvc_name)

            if _pvc_exists and not err:

                try:
                    body = kubernetes.client.V1DeleteOptions()
                    print("deleting pvc: %s"%pvc_name)
                    api_response = self.api.delete_namespaced_persistent_volume_claim(pvc_name,
                                                                         self.namespace,
                                                                         body)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
        return err

    def _pvc_exists(self,pvc_name):

        err = ""
        exists = False

        try:
            api_response = self.api.read_namespaced_persistent_volume_claim(pvc_name,
                                                               self.namespace)
            # if the pvc is found, no ApiException will be raised
            exists = True

        except ApiException as e:

            # the "Not Found" reason is the expected response it the pvc
            # does not exists. any other reason constitutes an error
            if e.reason != "Not Found":
                err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))

        return exists, err
