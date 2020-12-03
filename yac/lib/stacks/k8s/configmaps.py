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

class ConfigMaps(Resources):
    # a bunch of kubernetes configmaps

    def __init__(self,
                 serialized_kubernetes_stack):

        self.resource_array = search("configmaps",serialized_kubernetes_stack,[])

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

        # render intrinsics in configmaps
        rendered_configmaps = apply_intrinsics(self.resource_array, params)

        # render template variables in the body elements
        self.render_body_elements(rendered_configmaps)

        # save a hash of the rendered configmaps into the params for downstream
        # consumption
        set_configmaps_hash(rendered_configmaps,params)

        err = ""
        if dry_run_bool:
            return self._build_dryrun(rendered_configmaps,
                                      deploy_mode_bool)

        for configmap in rendered_configmaps:

            map_name = configmap['metadata']['name']

            _map_exists,err = self._map_exists(map_name)

            if not _map_exists and not err:

                # map does not yet exist
                # create it from scratch
                try:
                    api_response = self.api.create_namespaced_config_map(self.namespace,
                                                                         configmap)

                    print("configmap '%s' created"%map_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break

            elif _map_exists and not err:

                # map exists, so update it
                try:
                    api_response = self.api.replace_namespaced_config_map(map_name,
                                                                          self.namespace,
                                                                          configmap)

                    print("configmap '%s' updated"%map_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break
            else:
                err = "Exception when attempting to inspect the configmap %s:\n %s"%(map_name,err)
                break

        return err

    def _build_dryrun(self, configmaps_array, deploy_mode_bool):

        err = ""

        for configmap in configmaps_array:

            map_name = configmap['metadata']['name']

            _map_exists,err = self._map_exists(map_name)

            if not _map_exists and not err:
                print("configmap '%s' will be created as it does not yet exist"%map_name)
            elif _map_exists and not err:
                print("configmap '%s' will be updated"%map_name)
            else:
                err = "Exception when attempting to inspect the %s config_map: %s\n"%(map_name,err)
                break

        if not err:

            self.show_rendered_templates(configmaps_array,
                                         'configmap',
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

        # render intrinsics in configmaps
        rendered_configmaps = apply_intrinsics(self.resource_array, params)

        # save a hash of the configmaps into the params for downstream
        # consumption
        set_configmaps_hash(rendered_configmaps,params)

        for configmap in rendered_configmaps:

            map_name = configmap['metadata']['name']

            _map_exists,err = self._map_exists(map_name)

            if _map_exists and not err:

                try:
                    body = kubernetes.client.V1DeleteOptions()
                    print("deleting configmap: %s"%map_name)
                    api_response = self.api.delete_namespaced_config_map(map_name,
                                                                         self.namespace,
                                                                         body)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
        return err

    def _map_exists(self,map_name):

        err = ""
        exists = False

        try:
            api_response = self.api.read_namespaced_config_map(map_name,
                                                               self.namespace)
            # if the map is found, no ApiException will be raised
            exists = True

        except ApiException as e:

            # the "Not Found" reason is the expected response it the configmap
            # does not exists. any other reason constitutes an error
            if e.reason != "Not Found":
                err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))

        return exists, err

    def render_body_elements(self, configmaps_array):
        # render template variables in the body elements

        for configmap in configmaps_array:

            if 'data' in configmap:

                data_keys = list(configmap['data'].keys())

                for data_key in data_keys:

                    try:
                        # render template variables in this data element
                        configmap['data'][data_key] = apply_stemplate(configmap['data'][data_key], self.params)
                    except TemplateError as e:
                        print("configmap '%s' errors need fixing. exiting ..."%configmap['metadata']['name'])
                        print(e)
                        exit(1)

def get_configmaps_hash_key():
    return 'configmaps-hash'

def set_configmaps_hash(rendered_configmaps,params):

    # convert the rendered_configmaps into a string and create a hash of
    # the string. sort the keys to ensure that the dumped string is
    # always the same (as long as the contents of the dictionary is the same)

    configmaps_hash = str(hash(json.dumps(rendered_configmaps,sort_keys=True)))

    # save the hash back to the params
    params.set(get_configmaps_hash_key(),
               configmaps_hash,
               'a hash of the contents of ALL of the configmaps')

def get_configmaps_hash(params):

    # get the hash from the params
    return params.get(get_configmaps_hash_key())
