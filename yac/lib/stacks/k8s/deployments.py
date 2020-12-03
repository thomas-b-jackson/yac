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

class Deployments(Resources):
    # a bunch of kubernetes deployments

    def __init__(self,
                 serialized_kubernetes_stack):

        self.resource_array = search("deployments",serialized_kubernetes_stack,[])

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

        self.api = self.get_apps_api()

        # render intrinsics in deployments
        rendered_deployments = apply_intrinsics(self.resource_array, params)

        err = ""
        if dry_run_bool:
            return self.build_dryrun(rendered_deployments,
                                     deploy_mode_bool)

        for deployment in rendered_deployments:

            deployment_name = deployment['metadata']['name']

            deployment_exists,err = self.deployment_exists(deployment_name)

            if not deployment_exists and not err:

                # deployment does not yet exist
                # create it from scratch
                try:
                    api_response = self.api.create_namespaced_deployment(self.namespace,
                                                                         deployment)

                    print("deployment '%s' created"%deployment_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))

                    break

            elif deployment_exists and not err:

                # deployment exists, so update it
                try:
                    api_response = self.api.replace_namespaced_deployment(deployment_name,
                                                                          self.namespace,
                                                                          deployment)

                    print("deployment '%s' updated"%deployment_name)

                except ApiException as e:

                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break
            else:
                err = "Exception when attempting to inspect the deployment %s:\n %s"%(deployment_name,err)
                break

            # if we are error free AND this build is happening in the context of a
            # deploy, wait for pods to pass readiness
            if not err and deploy_mode_bool:
                err = self.wait(deployment_name, context)

        return err

    def wait(self, deployment_name, context):

        # use the kubectl rollout command to block until the deployment
        # rollout is complete
        kubectl_command = "kubectl --context=%s rollout status deployment/%s"%(context,deployment_name)

        print("waiting for rollout of '%s' deployment updates to complete ..."%deployment_name)
        output, err = self.run_kubectl(kubectl_command)

        if not err and 'successfully rolled out' not in output:
            err = output

        return err

    def build_dryrun(self, deployments_array, deploy_mode_bool):

        err = ""

        # print json.dumps(deployments_array,indent=2)

        for deployment in deployments_array:

            deployment_name = deployment['metadata']['name']

            deployment_exists,err = self.deployment_exists(deployment_name)

            if not deployment_exists and not err:
                print("deployment '%s' will be created as it does not yet exist"%deployment_name)
            elif deployment_exists and not err:
                print("deployment '%s' will be updated"%deployment_name)
            else:
                err = "Exception when attempting to inspect the %s deployment: %s\n"%(deployment_name,err)
                break

        if not err:

            self.show_rendered_templates(deployments_array,
                                         'deployment',
                                         deploy_mode_bool)

        return err

    def deployment_exists(self,deployment_name):

        err = ""
        exists = False

        try:
            api_response = self.api.read_namespaced_deployment(deployment_name,
                                                               self.namespace)
            # if the deployment is found, no ApiException will be raised
            exists = True

        except ApiException as e:

            # the "Not Found" reason is the expected response if the deployment
            # does not exists. any other reason constitutes an error
            if e.reason != "Not Found":
                err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))

        return exists, err

    def cost( self,
              params,
              context=""):

        total_cost=0
        if self.resource_array:
            # render intrinsics in deployments
            rendered_deployments = apply_intrinsics(self.resource_array, params)

            mem_cost_map = {
                "129M": 3.96
            }
            per_cpu_cost = 15.72

            resources = search("[*].spec.template.spec.resources.requests",rendered_deployments,[])
            pod_counts = search("[*].spec.replicas",rendered_deployments)

            mem_cost=0
            cpu_cost=0

            print("deployment cost is based on number of pods and memory and cpu requests for each")

            for i,resource in enumerate(resources):

                pod_count = float(pod_counts[i])
                if 'memory' in resource and resource['memory'] in mem_cost_map:
                    mem_cost = mem_cost_map[resource['memory']]
                if 'cpu' in resource:
                    cpu_cost = float(resource['cpu']) * per_cpu_cost

                total_cost = total_cost + 6.05*(pod_count * (mem_cost + cpu_cost))

            else:
                total_cost = total_cost + 6.05*(pod_count)

        return total_cost


    def pods_are_ready(self,deployname_name):

        all_pods_ready = True

        core_api = self.get_core_api()

        # for tracking that at least one pod associated with named deployment
        # exists
        a_deployment_pod_exists=False

        pod_list = core_api.list_namespaced_pod(self.namespace)

        for pod in pod_list.items:

            # naming convension for pods that are part of a deployment is to append
            # a unique id to the deployment name
            if deployname_name in pod.metadata.name:

                a_deployment_pod_exists = True
                pod_ready = self.status_pod(pod)

                if not pod_ready:
                    all_pods_ready = False
                    break

        return a_deployment_pod_exists and all_pods_ready

    def status_pod(self,pod):

        # pull the status of each container in the pod into a list of bools
        statuses = search("status.container_statuses[*].ready",pod.to_dict(),[])
        # make sure each all containers are ready
        pod_ready=False
        if statuses:
            pod_ready = False not in statuses

        print("pod: %s, ready?: %s"%(pod.metadata.name,pod_ready))

        return pod_ready

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

        # render intrinsics in deployments
        rendered_deployments = apply_intrinsics(self.resource_array, params)

        for deployment in rendered_deployments:

            deployment_name = deployment['metadata']['name']

            _deployment_exists,err = self.deployment_exists(deployment_name)

            if _deployment_exists and not err:

                try:
                    body = kubernetes.client.V1DeleteOptions()
                    print("deleting deployment: %s in namespace: %s"%(deployment_name,self.namespace))
                    api_response = self.api.delete_namespaced_deployment(deployment_name,
                                                                     self.namespace,
                                                                     body,
                                                                     propagation_policy='Orphan')

                except ApiException as e:
                    err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))
                    break
        return err