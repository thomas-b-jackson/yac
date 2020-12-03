from yac.lib.input import string_validation
from yac.lib.file import load_dict_from_file
from yac.lib.intrinsic import apply_intrinsics

def get_builder_resources(k8s_stack, params):
    # args
    #    k8s_stack: and instance of the K8sStack class
    #    params: an instance of the Params class

    # calculate an appropriate set of rules for this k8s stack
    rules = get_recommended_rules(k8s_stack)
    resources = {}
    builder_account_name = ""

    if rules:
        # get the build account name
        builder_account_name = get_builder_account_name(params)

        # load the resource templates
        resources = load_yaml()

        params.set("builder-name", builder_account_name)
        params.set("builder-rules", rules)

    return resources,builder_account_name

def get_builder_account_name(params):

    # we should only need one builder per cluster
    # use a builder with the same name as the service, but
    # with a builder suffix

    default_alias = params.get("service-default-alias")

    builder_account_name = "%s-%s"%(default_alias,'builder')

    return builder_account_name

def load_yaml():
    # load the sa, role, and rolebinding resource templates
    # from file
    builder_resources,err = load_dict_from_file("yac/lib/stacks/k8s/configs/builder.yaml")

    return builder_resources

def get_recommended_rules(k8s_stack):

    mgr = GroupManager()

    resource_types = get_resource_types(k8s_stack)

    for resource in resource_types:
        mgr.add_resource(resource)

    recommended_rules = mgr.create_rules()

    return recommended_rules

def get_resource_types(k8s_stack):

    resources_types =[]

    if k8s_stack.deployments.resource_array:
        resources_types.append("deployments")
    if k8s_stack.statefulsets.resource_array:
        resources_types.append("statefulsets")
    if (k8s_stack.deployments.resource_array or k8s_stack.statefulsets.resource_array):
        resources_types.append("pods")
    if k8s_stack.services.resource_array:
        resources_types.append("services")
    if k8s_stack.ingresses.resource_array:
        resources_types.append("ingresses")
    if k8s_stack.configmaps.resource_array:
        resources_types.append("configmaps")
    if k8s_stack.secrets.resource_array:
        resources_types.append("secrets")

    return resources_types

class GroupManager():

    def __init__(self):

        # maps group to the resources they apply to
        self.group_map = {
            "core": ["pods", "secrets", "configmaps", "services", "persistentvolumeclaims"],
            "extensions": ["ingresses"],
            "extension/apps": ["deployments","statefulsets"]
        }
        self.verbs = ["create", "get", "list", "patch", "update", "watch"]

        # maps group keys to the actual group array used by k8s in
        # permissioning
        self.group_array_map = {
            "core": [""],
            "extensions": ["extensions"],
            "extension/apps": ["extensions","apps"]
        }

        # maps groups to the resources in the service's stack
        self.resources_map = {
            "core": [],
            "extensions": [],
            "extension/apps": []
        }

    def add_resource(self,resource):

        # get the group this resource is associated with
        for group_key in list(self.group_map.keys()):
            if resource in self.group_map[group_key]:
                self.resources_map[group_key].append(resource)

    def create_rules(self):

        rules = []

        for key in list(self.resources_map.keys()):
            if self.resources_map[key]:
                rules.append({
                    "apiGroups": self.group_array_map[key],
                    "resources": self.resources_map[key],
                    "verbs": self.verbs
                    })

        return rules


