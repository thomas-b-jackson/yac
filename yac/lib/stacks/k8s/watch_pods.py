import os, time, json
# from kubernetes import client, config, watch
import kubernetes.client
import kubernetes.config
from yac.lib.search import search

def status_pod(pod):

    # pull the status of each container in the pod into a list of bools
    statuses = search("status.container_statuses[*].ready",pod.to_dict())
    # make sure each container is status=True
    pod_ready = False not in statuses
    print("pod: %s, ready?: %s"%(pod.metadata.name,pod_ready))

    return pod_ready

def pods_are_ready(deployname_name):

    all_pods_ready = True

    # for tracking that at least one pod associated with named deployment
    # exists
    a_deployment_pod_exists=False

    pod_list = api.list_namespaced_pod("sets")

    for pod in pod_list.items:

        if deployname_name in pod.metadata.name:

            a_deployment_pod_exists = True
            pod_ready = status_pod(pod)

            if not pod_ready:
                all_pods_ready = False
                break
    
    return a_deployment_pod_exists and all_pods_ready


kubernetes.config.load_kube_config(context="prod")
api = kubernetes.client.CoreV1Api()

deployment_name = "jira-dev-1"

while not pods_are_ready(deployment_name):

    # sleep for 10 seconds then try again
    print("pod(s) not ready ... checking back in 10 seconds ...")
    time.sleep(10)
