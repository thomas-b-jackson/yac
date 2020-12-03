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

class StatefulSets(Resources):
    # a bunch of kubernetes statefulsets

    def __init__(self,
                 serialized_kubernetes_stack):

        self.resource_array = search("statefulsets",serialized_kubernetes_stack,[])

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

        # statefulset apis live under AppsV1beta1Api
        self.api = self.get_apps_api()

        # render intrinsics in statefulsets
        rendered_statefulsets = apply_intrinsics(self.resource_array, params)

        err = ""
        if dry_run_bool:
            return self.build_dryrun(rendered_statefulsets, deploy_mode_bool)

        for statefulset in rendered_statefulsets:

            statefulset_name = statefulset['metadata']['name']

            statefulset_exists,err = self.statefulset_exists(statefulset_name)

            if not statefulset_exists and not err:

                # statefulset does not yet exist
                # create it from scratch
                try:
                    api_response = self.api.create_namespaced_stateful_set(self.namespace,
                                                                         statefulset)

                    print("statefulset '%s' created"%statefulset_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break

            elif statefulset_exists and not err:

                # statefulset exists, so update it
                try:
                    api_response = self.api.replace_namespaced_stateful_set(statefulset_name,
                                                                          self.namespace,
                                                                          statefulset)

                    print("statefulset '%s' updated"%statefulset_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break
            else:
                err = "Exception when attempting to inspect the statefulset %s:\n %s"%(statefulset_name,err)
                break

            # if we are error free AND this build is happening in the context of a
            # deploy, wait for pods to pass readiness
            if not err and deploy_mode_bool:
                self.wait(statefulset_name)

        return err

    def wait(self, statefulset_name):

        for pod_name in self.get_pod_names(statefulset_name):

            # sleep for 10 seconds to wait for scheduler to have time to react
            # to statefulset changes that motivate pod restarts
            print("waiting 10 seconds for scheduler to roll pod %s (may or may not be necessary)..."%pod_name)
            time.sleep(10)

            while not self.pods_are_ready(statefulset_name):

                # sleep for 10 seconds then try again
                print("pod %s not ready ... will check back in 10 seconds ..."%pod_name)
                time.sleep(10)

    def build_dryrun(self, statefulset_array, deploy_mode_bool):

        err = ""

        for statefulset in statefulset_array:

            statefulset_name = statefulset['metadata']['name']

            statefulset_exists,err = self.statefulset_exists(statefulset_name)

            if not statefulset_exists and not err:
                print("statefulset '%s' will be created as it does not yet exist"%statefulset_name)
            elif statefulset_exists and not err:
                print("statefulset '%s' will be updated"%statefulset_name)
            else:
                err = "Exception when attempting to inspect the %s statefulset: %s\n"%(statefulset_name,e)
                break

        if not err:

            self.show_rendered_templates(statefulset_array,
                                         'statefulset',
                                         deploy_mode_bool)

        return err

    def statefulset_exists(self,statefulset_name):

        err = ""
        exists = False

        try:
            api_response = self.api.read_namespaced_stateful_set(statefulset_name,
                                                               self.namespace)
            # if the statefulset is found, no ApiException will be raised
            exists = True

        except ApiException as e:

            # the "Not Found" reason is the expected response if the statefulset
            # does not exists. any other reason constitutes an error
            if e.reason != "Not Found":
                err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))

        return exists, err

    def status_pod(self,pod):

        # pull the status of each container in the pod into a list of bools
        statuses = search("status.container_statuses[*].ready",pod.to_dict(),[])

        print("pod statuses: %s"%statuses)

        # make sure each container is status=True
        pod_ready = statuses and (False not in statuses)
        print("pod: %s, ready?: %s"%(pod.metadata.name,pod_ready))

        return pod_ready

    def get_pod_names(self,statefulset_name):

        pod_names = []
        core_api = self.get_core_api()

        pod_list = core_api.list_namespaced_pod(self.namespace)

        for pod in pod_list.items:

            # naming convension for pods that are part of a statefulset is to append
            # a unique id to the statefulset name
            if statefulset_name in pod.metadata.name:
                pod_names.append(pod.metadata.name)

        return pod_names

    def pods_are_ready(self,statefulset_name):

        all_pods_ready = True

        core_api = self.get_core_api()

        # for tracking that at least one pod associated with named statefulset
        # exists
        a_statefulset_pod_exists=False

        pod_list = core_api.list_namespaced_pod(self.namespace)

        for pod in pod_list.items:

            # naming convension for pods that are part of a statefulset is to append
            # a unique id to the statefulset name
            if statefulset_name in pod.metadata.name:

                a_statefulset_pod_exists = True
                pod_ready = self.status_pod(pod)

                if not pod_ready:
                    all_pods_ready = False
                    break

        return a_statefulset_pod_exists and all_pods_ready

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

        self.api = self.get_apps_api()

        # render intrinsics in the statefulsets
        rendered_sets = apply_intrinsics(self.resource_array, params)

        for statefulset in rendered_sets:

            statefulset_name = statefulset['metadata']['name']

            _statefulset_exists,err = self.statefulset_exists(statefulset_name)

            if _statefulset_exists and not err:

                try:
                    body = kubernetes.client.V1DeleteOptions()
                    print("deleting statefulset: %s"%statefulset_name)
                    api_response = self.api.delete_namespaced_stateful_set(statefulset_name,
                                                                     self.namespace,
                                                                     body,
                                                                     propagation_policy='Orphan')

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
        return err