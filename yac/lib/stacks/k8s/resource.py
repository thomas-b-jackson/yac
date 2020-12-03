#!/usr/bin/env python
import json, subprocess
import urllib3 # for temporarily disabling insecure tls warnings
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException
from pprint import pprint
from yac.lib.search import search
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.file import dump_dictionary
from yac.lib.stacks.k8s.credentials import load_context as load_context_ext

class Resources():

    def __init__(self,
                 serialized_kubernetes_stack,
                 namespace=""):

        self.resource_array = search("resources",serialized_kubernetes_stack,[])

        self.namespace = namespace

    def add(self,
            resource):
        if resource.resource_array:
            self.resource_array = self.resource_array + resource.resource_array

    def build(self,
              params,
              deploy_mode_bool=False,
              context=""):

        self.params = params

        # render intrinsics in resources
        rendered_resources = apply_intrinsics(self.resource_array, params)

        err = ""
        for resource in rendered_resources:

            resource_name = ""
            kind = ""

            if 'metadata' in resource and 'name' in resource['metadata']:
                resource_name = resource['metadata']['name']
                print("building resource %s"%resource_name)
            else:
                print("resource lacks a 'name' attribute. aborting")
                break

            if 'kind' in resource:
                kind = resource['kind']
            else:
                err = "resource lacks a 'kind' attribute. aborting"
                break

            resource_exists,err = self.resource_exists(resource_name,kind)

            if resource_exists:
                action = "apply"
            else:
                action = "create"

            resource_file_path = dump_dictionary(resource,
                                                 self.params.get("servicefile-path"),
                                                 "%s.json"%kind.lower())

            contextual_action_str = self.get_context_str(action, context)

            kubectl_command = "kubectl %s -f %s"%(contextual_action_str,
                                                  resource_file_path)

            output, err = self.run_kubectl(kubectl_command)

            if not err:
                print("%s '%s' created"%(kind,resource_name))
            else:
                err = "build of '%s' resource '%s' failed with error: %s. aborting"%(kind,resource_name,err)
                break

        return err

    def delete(self, context, params):

        self.params = params

        # render intrinsics in resources
        rendered_resources = apply_intrinsics(self.resource_array, params)

        err = ""
        for resource in rendered_resources:

            resource_name = ""
            kind = ""

            if 'metadata' in resource and 'name' in resource['metadata']:
                resource_name = resource['metadata']['name']
            else:
                err = "resource lacks a 'name' attribute. aborting"
                break

            if 'kind' in resource:
                kind = resource['kind']
            else:
                err = "resource lacks a 'kind' attribute. aborting"
                break

            resource_exists,err = self.resource_exists(resource_name,kind)

            if resource_exists:

                resource_file_path = dump_dictionary(resource,
                                                     self.params.get("servicefile-path"),
                                                     "%s.json"%kind.lower())

                contextual_action_str = self.get_context_str("delete", context)

                kubectl_command = "kubectl %s -f %s"%(contextual_action_str,
                                                      resource_file_path)

                output, err = self.run_kubectl(kubectl_command)

                if not err:
                    print("%s '%s' deleted"%(kind,resource_name))
                else:
                    err = "deletion of '%s' resource '%s' failed with error: %s. aborting"%(kind,resource_name,err)
                    break

        return err

    def run_kubectl(self, kubectl_command):

        err = ""
        output = ""

        # the subprocess run command expects the command to be split into an array
        # on whitespace boundaries.
        kubectl_command_array = kubectl_command.split(" ")

        try:

            completed_process = subprocess.run(kubectl_command_array,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       text=True)

            # get stdout as string
            output = completed_process.stdout

        except Exception as e:

            err = str(e)

        if "error" in output:
            err = output

        return output, err

    def dryrun(self,
               params,
               deploy_mode_bool=False,
               context=""):

        err = ""

        self.params = params

        # render intrinsics in resources
        rendered_resources = apply_intrinsics(self.resource_array, params)

        for resource in rendered_resources:

            if 'metadata' in resource and 'name' in resource['metadata']:
                resource_name = resource['metadata']['name']
                print("building resource %s"%resource_name)
            else:
                err = "resource lacks a name. aborting"
                break

            if 'kind' in resource:
                kind = resource['kind']
            else:
                err = "resource lacks a kind attribute. aborting"
                break

            resource_exists,err = self.resource_exists(resource_name,kind)
            if not resource_exists and not err:
                print("'%s' resource '%s' will be created as it does not yet exist"%(kind,resource_name))
            elif resource_exists and not err:
                print("'%s' resource '%s' will be updated"%(kind,resource_name))
            else:
                err = "Exception when attempting to inspect the %s %s resource: %s\n"%(resource_name,
                                                                                       kind,
                                                                                       err)
                break

        if not err:

            self.show_rendered_templates(rendered_resources,
                                         'resources',
                                         deploy_mode_bool)

        return err

    def resource_exists(self,resource_name, kind):

        kubectl_command = "kubectl get %s %s"%(kind, resource_name)

        output, err = self.run_kubectl(kubectl_command)

        exists = False if 'NotFound' in output else True

        return exists, err

    def get_core_api(self):

        # TODO: remove the self.get_insecure_tls_config() call once the nonprod
        #  public api get's its certs fixed, i.e.:
        #  return kubernetes.client.CoreV1Api()
        return kubernetes.client.CoreV1Api(self.get_insecure_tls_config())

    def get_apps_api(self):

        # TODO: remove the self.get_insecure_tls_config() call once the nonprod
        #  public api gets its certs fixed, i.e.:
        #  return kubernetes.client.AppsV1Api()
        return kubernetes.client.AppsV1Api(self.get_insecure_tls_config())

    def get_extensions_api(self):

        # TODO: remove the self.get_insecure_tls_config() call once the nonprod
        #  public api gets its certs fixed, i.e.:
        #  return kubernetes.client.AppsV1Api()
        return kubernetes.client.ExtensionsV1beta1Api(self.get_insecure_tls_config())

    def get_insecure_tls_config(self):
        # disable tls when making api calls

        configuration = kubernetes.client.Configuration()
        configuration.verify_ssl = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return kubernetes.client.ApiClient(configuration)

    def get_context_str(self,
                        action,
                        context):
        # create a 'contextual' action string for use in a kubectl call
        # the string combines what action with what cluster context

        if context:
            context_str = "%s --context=%s"%(action,context)
        else:
            context_str = action

        return context_str

    def show_rendered_templates(self,
                                resource_array,
                                resource_type,
                                deploy_mode_bool):

        if resource_array:

            print_template = 'y'

            if not deploy_mode_bool:

                print_template = input("Print %s templates to stdout? (y/n)> "%resource_type)

            if print_template and print_template=='y':

                # pretty-print rendered resources
                print(json.dumps(resource_array,indent=2))


    def serialize(self):

        return self.resource_array

    def __str__(self):

        return json.dumps(self.serialize(),indent=2)
