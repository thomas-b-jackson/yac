#!/usr/bin/env python
import json, copy, time, socket
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException
from yac.lib.search import search
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.stacks.k8s.resource import Resources
from yac.lib.stacks.k8s.credentials import load_context, get_current_namespace
from pprint import pprint

class Services(Resources):
    # a bunch of kubernetes services

    def __init__(self,
                 serialized_kubernetes_stack):

        self.resource_array = search("services",serialized_kubernetes_stack,[])

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

        # render intrinsics in services
        services_copy = apply_intrinsics(self.resource_array, params)

        err = ""
        if dry_run_bool:
            return self._build_dryrun(services_copy, deploy_mode_bool)

        for service in services_copy:

            service_name = service['metadata']['name']

            _service_exists,err = self._service_exists(service_name)

            if not _service_exists and not err:

                # service does not yet exist
                # create it from scratch
                try:
                    api_response = self.api.create_namespaced_service(self.namespace,
                                                                         service)

                    print("service '%s' created"%service_name)

                except ApiException as e:

                    err = "Exception when creating service %s:\n %s"%(service_name,e)
                    break

            elif _service_exists and not err:

                # service exists, and services are immutable.
                print("service '%s' already exists. services are immutable, "%service_name)
                print(" so if you want it replaced, delete it manually then re-build the stack")

            else:
                err = "Exception when attempting to inspect the service %s:\n %s"%(service_name,e)
                break

            # if we are error free AND this build is happening in the context of a
            # deploy, wait for svc to resolve
            if not err and deploy_mode_bool:
                self.wait(service_name)

        return err

    def wait(self, service_name):

        v1_service = self.api.read_namespaced_service(service_name,
                                                   self.namespace)

        if v1_service and v1_service.spec.type == 'LoadBalancer':

            # svc type=LB include an ELB
            # wait for:
            # 1. the ELB to be assigned, and
            # 2. the ELB hostname to start resolving via DNS

            while (not v1_service.status or
                   not v1_service.status.load_balancer or
                   not v1_service.status.load_balancer.ingress or
                   len(v1_service.status.load_balancer.ingress) != 1):

                # sleep for 10 seconds then try again
                print("%s svc not ready ... will check back in 10 seconds ..."%service_name)
                time.sleep(10)

                v1_service = self.api.read_namespaced_service(service_name,
                                                         self.namespace)

            hostname = v1_service.status.load_balancer.ingress[0].hostname

            # wait for hostname to start resolving
            while (not hostname_resolves(hostname)):
                # sleep for 10 seconds then try again
                print("hostname %s not yet resolving ... will check back in 10 seconds ..."%hostname)
                time.sleep(10)

    def _build_dryrun(self, services_array, deploy_mode_bool):

        err = ""

        for service in services_array:

            service_name = service['metadata']['name']

            _service_exists,err = self._service_exists(service_name)

            if not _service_exists and not err:
                print("service '%s' will be created as it does not yet exist"%service_name)
            elif _service_exists and not err:
                print("service '%s' will be updated"%service_name)
            else:
                err = "Exception when attempting to inspect the %s service: %s\n"%(service_name,err)
                break

        if not err:

            self.show_rendered_templates(services_array,
                                         'service',
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

        # render intrinsics in the services
        rendered_svcs = apply_intrinsics(self.resource_array, params)

        for service in rendered_svcs:

            service_name = service['metadata']['name']

            _service_exists,err = self._service_exists(service_name)

            if _service_exists and not err:

                try:
                    body = kubernetes.client.V1DeleteOptions()
                    print("deleting service: %s in namespace: %s"%(service_name,self.namespace))
                    api_response = self.api.delete_namespaced_service(service_name,
                                                                      self.namespace,
                                                                      body)

                except ApiException as e:

                    err = e
        return err

    def _service_exists(self,service_name):

        err = ""
        exists = False

        try:
            api_response = self.api.read_namespaced_service(service_name,
                                                               self.namespace)
            # if the map is found, no ApiException will be raised
            exists = True

        except ApiException as e:

            # the "Not Found" reason is the expected response it the service
            # does not exists. any other reason constitutes an error
            if e.reason != "Not Found":
                err = "\n%s"%(json.dumps(json.loads(e.body),indent=2))

        return exists, err

def hostname_resolves(hostname):
    try:
        socket.gethostbyname(hostname)
        return 1
    except socket.error:
        return 0