#!/usr/bin/env python
import json, copy, base64
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException
from pprint import pprint
from yac.lib.search import search
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.template import apply_stemplate, TemplateError
from yac.lib.stacks.k8s.resource import Resources
from yac.lib.stacks.k8s.credentials import load_context, get_current_namespace

class Secrets(Resources):
    # a bunch of kubernetes secrets

    def __init__(self,
                 serialized_kubernetes_stack):

        self.resource_array = search("secrets",serialized_kubernetes_stack,[])

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

        # render intrinsics in secrets
        rendered_secrets = apply_intrinsics(self.resource_array, params)

        # render template variables in the body elements
        self.render_body_elements(rendered_secrets)

        # save a hash of the rendered secrets into the params for downstream
        # consumption
        set_secrets_hash(rendered_secrets,params)

        err = ""
        if dry_run_bool:
            return self.build_dryrun(rendered_secrets, deploy_mode_bool)

        for secret in rendered_secrets:

            secret_name = secret['metadata']['name']

            secret_exists,err = self.secret_exists(secret_name)

            if not secret_exists and not err:

                # secret does not yet exist
                # create it from scratch
                try:
                    api_response = self.api.create_namespaced_secret(self.namespace,
                                                                         secret)

                    print("secret '%s' created"%secret_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break

            elif secret_exists and not err:

                # secret exists, so update it
                try:
                    api_response = self.api.replace_namespaced_secret(secret_name,
                                                                          self.namespace,
                                                                          secret)

                    print("secret '%s' updated"%secret_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break
            else:
                err = "Exception when attempting to inspect the secret %s:\n %s"%(secret_name,err)
                break

        return err

    def build_dryrun(self, secrets_array, deploy_mode_bool):

        err = ""

        for secret in secrets_array:

            secret_name = secret['metadata']['name']

            secret_exists,err = self.secret_exists(secret_name)

            if not secret_exists and not err:
                print("secret '%s' will be created as it does not yet exist"%secret_name)
            elif secret_exists and not err:
                print("secret '%s' will be updated"%secret_name)
            else:
                err = "Exception when attempting to inspect the %s secret: %s\n"%(secret_name,e)
                break

        if not err:

            self.show_rendered_templates(secrets_array,
                                         'secret',
                                         deploy_mode_bool)

        return err

    def secret_exists(self,secret_name):

        err = ""
        exists = False

        try:
            api_response = self.api.read_namespaced_secret(secret_name,
                                                               self.namespace)
            # if the secret is found, no ApiException will be raised
            exists = True

        except ApiException as e:

            # the "Not Found" reason is the expected response it the secret
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

        self.api = self.get_core_api()

        # render intrinsics in secrets
        rendered_secrets = apply_intrinsics(self.resource_array, params)

        # save a hash of the rendered secrets into the params for downstream
        # consumption
        set_secrets_hash(rendered_secrets, params)

        for secret in rendered_secrets:

            secret_name = secret['metadata']['name']

            _secret_exists,err = self.secret_exists(secret_name)

            if _secret_exists and not err:

                try:
                    body = kubernetes.client.V1DeleteOptions()
                    print("deleting secret: %s"%secret_name)
                    api_response = self.api.delete_namespaced_secret(secret_name,
                                                                     self.namespace,
                                                                     body)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
        return err

    def render_body_elements(self, secrets_array):
        # render template variables in the body elements

        for secret in secrets_array:

            if 'data' in secret:

                data_keys = list(secret['data'].keys())

                for data_key in data_keys:

                    try:
                        # render template variables in this data element
                        secret['data'][data_key] = apply_stemplate(secret['data'][data_key], self.params)
                    except TemplateError as e:
                        print("secret '%s' errors need fixing. exiting ..."%secret['metadata']['name'])
                        print(e)
                        exit(1)


    def get_secret_value(self,
                         context,
                         secret_name,
                         field):

        err = ""
        secret_value = ""

        # load context
        err = load_context(context)

        # do not proceed if context could not be loaded
        if err:
            return secret_value,err

        # get the namespace from the current context
        self.namespace, err = get_current_namespace()

        # do not proceed if namespace not found
        if err:
            return secret_value,err

        self.api = self.get_core_api()

        try:

            api_response = self.api.read_namespaced_secret(secret_name,
                                                          self.namespace)

            secret_data = api_response.data

            # if the secret is found, no ApiException will be raised
            if field in secret_data:
                secret_value = base64.b64decode(secret_data[field])

        except ApiException as e:

            # the "Not Found" reason is the expected response it the secret
            # does not exists. any other reason constitutes an error
            if e.reason != "Not Found":
                err = e
            print(e)

        return secret_value, err

def get_secrets_hash_key():
    return 'secrets-hash'

def set_secrets_hash(rendered_secrets,params):

    # convert the rendered_secrets into a string and create a hash of
    # the string. sort the keys to ensure that the dumped string is
    # always the same (as long as the contents of the dictionary is the same)

    secrets_hash = str(hash(json.dumps(rendered_secrets,sort_keys=True)))

    # save the hash back to the params
    params.set(get_secrets_hash_key(),
               secrets_hash,
               'a hash of the contents of ALL of the secrets')

def get_secrets_hash(params):

    # get the hash from the params
    return params.get(get_secrets_hash_key())