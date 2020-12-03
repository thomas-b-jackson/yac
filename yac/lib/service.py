import os, json, copy, sys
from yac.lib.registry import get_registry_keys, get_remote_value
from yac.lib.registry import clear_entry_w_challenge, set_remote_string_w_challenge
from yac.lib.file import get_file_contents, load_dict_from_file
from yac.lib.file import register_file,get_file_abs_path
from yac.lib.file_converter import convert_local_files, find_and_delete_remotes
from yac.lib.search import search
from yac.lib.intrinsic import apply_custom_fxn
from yac.lib.schema import validate
from yac.lib.stack import Stack
from yac.lib.inputs import Inputs, InputsCacher
from yac.lib.secrets import Secrets
from yac.lib.vault import SecretVaults
from yac.lib.params import Params
from yac.lib.task import Tasks
from yac.lib.artifacts import Artifacts
from yac.lib.test import IntegrationTests
from yac.lib.inputs import Inputs
from yac.lib.credentials import Credentialers
from yac.lib.pipeline import Pipeline

PARAMS_CACHE_SUFFIX = "params"

class ServiceError():
    def __init__(self, msg):
        self.msg = msg

class Service():

    def __init__(self,
                 serialized_service,
                 service_path,
                 alias="",
                 params_path="",
                 kvps=""):

        # first validate. this should throw an exception if
        # required fields aren't present
        validate(serialized_service, "yac/schema/service.json")

        self.path = service_path
        self.kvps_str = kvps
        self.params_file_path = params_path

        self.description = Description(search('Description',
                                       serialized_service,{}),
                                       alias)

        self.vaults = SecretVaults(search('"Vaults"',
                                      serialized_service,[]))

        # a service can references other services that it includes
        self.includes = search("includes",
                             serialized_service,{})

        # initialize stack params (key/value pairs and maps), including static params specified
        # in the serialized service, params from an external file,
        # params specified in a key-value pair string (kvps),
        self.params = Params(search('"Params"',
                                    serialized_service, {}))

        # initialize the dictionary that will hold all params (statics+secrets+inputs)
        self.all_params = {}

        inputs_cacher = InputsCacher(search('InputsCache',
                                    serialized_service,{}))

        self.inputs = Inputs(search('Inputs',
                                    serialized_service,{}),
                             inputs_cacher)

        self.secrets = Secrets(search('"Secrets"',
                                      serialized_service,{}))

        # inialize the stack associated with this service
        self.stack = Stack(search('Stack',
                                  serialized_service, {}))

        self.tasks = Tasks(search('Tasks',
                                    serialized_service,{}))

        # initialize the tests associated with this service
        self.tests = IntegrationTests(search('"IntegrationTests"',
                                      serialized_service,{}))

        # initialize the artifacts associate with this service
        self.artifacts = Artifacts(search('Artifacts',
                                           serialized_service,[]))

        # initialize the credentialer associated with this service
        self.credentialers = Credentialers(search("Credentialers",serialized_service,[]))

        # initialize the pipeline associated with this service
        self.pipeline = Pipeline(search('Pipeline',
                                     serialized_service,{}))

        # load the objects from each included service
        self.load_includes()

        # save a copy of the full serialized version of the
        # service to support the serialize() method
        self.serialized_service = serialized_service

    # add mergeable fields from another service into this service
    def add(self,
            service):

        if service.params:

            self.params.add(service.params)

        if service.secrets:

            self.secrets.add(service.secrets)

        if service.vaults:

            self.vaults.add(service.vaults)

        if service.stack.impl:

            # there can be only one stack
            if self.stack.impl:
                self.stack.add(service.stack)
            else:
                self.stack = service.stack

        if service.tasks:

            self.tasks.add(service.tasks)

        if service.inputs:

            self.inputs.add(service.inputs)

        if service.tests:

            self.tests.add(service.tests)

        if service.artifacts:

            self.artifacts.add(service.artifacts)

        if service.credentialers:

            self.credentialers.add(service.credentialers)

        if service.pipeline and service.pipeline.get_stages():

            # there can be only one pipeline per service
            self.pipeline = service.pipeline

    def add_params_via_kvps(self,kvp_str):
        # load key-value pairs via a kvp string formatted as:
        # <key1>:<value1>,<key2>:<val2>,etc
        self.params.load_kvps(kvp_str)

    def load_includes(self):
        # load objects from each included service

        # for each included service specified
        for service_key in self.includes:

            sub_service_path = self.includes[service_key]["value"]

            # load the included service ...
            this_sub, err = get_service(sub_service_path,
                                   servicefile_path=self.path)

            # add to this service
            if not err:
                print("including '%s' service ..."%(service_key))
                self.add(this_sub)
            else:
                print("included service '%s' could not be loaded from %s"%(service_key,
                                                                           sub_service_path))
                print("error: %s"%err)
                print("exiting ...")
                exit(0)

                exit(0)

    def get_meta_params(self):
        # get meta data about this service

        service_metadata = Params({})
        service_metadata.set("service-default-alias",self.description.default_alias, "service default alias")
        service_metadata.set("service-alias",self.description.alias, "service alias")
        service_metadata.set("service-name",self.description.name, "service name")

        service_metadata.set("servicefile-path",self.path, "path to the servicefile")

        # add service summary and repo
        service_metadata.set('service-summary',self.description.summary, "service summary")
        service_metadata.set('service-repo',self.description.repo, "repo containing this service")

        # add the command that was run against this service
        service_metadata.set("yac-command",sys.argv[0], 'the yac command being run')

        return service_metadata

    def get_params(self):

        # add params describing the service itself
        self.params.add(self.get_meta_params())

        # load any params from yac-supported env variables
        self.params.load_from_env_variables()

        # load kvps (typically used for injecting inputs in pipelines or overriding
        #   an invidual param setpoint)
        self.params.load_kvps(self.kvps_str)

        # load params from file
        self.params.load_from_file(self.params_file_path)

        return self.params

    def get_all_params(self,
                       context="",
                       dry_run_bool=False,
                       credentialer_names=[]):

        # Take a copy of params
        self.all_params = self.get_params()

        # process inputs and load results into params
        self.inputs.load(self.all_params)

        # load secrets into params
        self.secrets.load(self.all_params,
                          self.vaults)

        return self.all_params

    def get_description(self):

        return self.description

    def get_artifacts(self):

        return self.artifacts

    def get_stack(self):

        return self.stack

    def get_tests(self):

        return self.tests

    def get_tasks(self):

        return self.tasks

    def get_vaults(self):

        return self.vaults

    def get_deployer(self):

        return self.deployer()

    def get_inputs(self):

        return self.inputs

    def get_secrets(self):

        return self.secrets

    def get_pipeline(self):

        return self.pipeline

    def get_credentialers(self):

        return self.credentialers

    def get_serialized_pipeline(self):

        return self.serialized_pipeline

    def deploy_boot_files(self, dry_run_bool=False):

        self.boot_files.deploy(self.params, dry_run_bool)

    def serialize(self):
        return self.serialized_service

    def __str__(self):
        ret = ("description:\n %s\n"%self.description +
               "params:\n %s\n"%self.params +
               "secrets:\n %s\n"%self.secrets +
               "stack:\n %s\n"%self.stack +
               "vaults: \n %s\n")%self.vaults
        return ret

class Description():

    def __init__(self,
                 serialized_service_description,
                 alias):

        validate(serialized_service_description,
                "yac/schema/description.json")

        self.name = search('"name"',
                            serialized_service_description,"")

        self.summary = search('summary',
                              serialized_service_description,"")

        self.version = search('version',
                              serialized_service_description,"")

        self.repo = search('repo',
                            serialized_service_description,"")

        self.default_alias = search('"default-alias"',
                                serialized_service_description,"")
        if alias:
            self.alias = alias
        else:
            self.alias = self.default_alias

    def get_alias(self):
        return self.alias

    def __str__(self):
        ret = ("name:\n %s\n"%self.name +
               "summary:\n %s\n"%self.summary +
               "version:\n %s\n"%self.version +
               "repo:\n %s\n"%self.repo +
               "alias: \n %s\n")%self.alias

        return ret

def get_service(servicefile_arg,
                alias="",
                params_file_path="",
                kvp_str="",
                servicefile_path=""):

    # treat the arg as a path to a local file
    service,err = get_service_from_file(servicefile_arg,
                                    servicefile_path,
                                    alias,
                                    params_file_path,
                                    kvp_str)

    if err:

        # Service does not exist as a local file
        service_name = ""

        # Treat servicefile_arg as the service name. See if it is complete (i.e.
        # includes a version label)
        if is_service_name_complete(servicefile_arg):

            # name is complete
            service_name = servicefile_arg

        # Treat servicefile_arg is a service name that lacks a version
        elif is_service_available_partial_name(servicefile_arg):

            # get complete name
            service_name = get_complete_name(servicefile_arg)

        if service_name:

            # pull the service from the registry
            service = get_service_by_name(service_name,
                                        alias,
                                        params_file_path,
                                        kvp_str)

    return service, err

def get_service_from_file(servicefile_arg,
                          servicefile_path="",
                          alias_arg="",
                          params_file_path="",
                          kvp_arg=""):

    service = None

    serialized_service,err = load_dict_from_file(servicefile_arg,
                                                 servicefile_path)

    # pull the service descriptor from file
    if not err:

        # the servicefile_arg could be relative to servicefile_path (if
        # this is a local sub-service) or absolute
        # determine the absolute path for either condition
        serivcefile_abs_path = get_file_abs_path(servicefile_arg,
                                                 servicefile_path)

        service = Service(serialized_service,
                          serivcefile_abs_path,
                          alias_arg,
                          params_file_path,
                          kvp_arg)

    return service, err

def get_service_by_name(service_name,
                        alias_arg="",
                        params_file_path="",
                        kvp_str=""):

    service = None

    if service_name:

        reg_key = service_name + YAC_SERVICE_SUFFIX

        # look in remote registry
        service_contents = get_remote_value(reg_key)

        if service_contents:

            # load into dictionary
            serialized_service = json.loads(service_contents)

            service = Service(serialized_service,
                              "",
                              alias_arg,
                              params_file_path,
                              kvp_str)

    return service


def clear_service(service_name, challenge):

    # if service is in fact registered
    service = get_service_by_name(service_name)

    if service:

        # clear service entry registry
        reg_key = service_name + YAC_SERVICE_SUFFIX
        clear_entry_w_challenge(reg_key, challenge)

        # clear any files referenced
        find_and_delete_remotes(service.serialize(), challenge)

    else:
        raise ServiceError("service with key %s doesn't exist"%service_name)

# register service into yac registry
def register_service(service_name, servicefile_w_path, challenge):

    err = ""
    if os.path.exists(servicefile_w_path):

        service_contents_str = get_file_contents(servicefile_w_path)

        if service_contents_str:

            reg_key = service_name + YAC_SERVICE_SUFFIX

            # get the base path of the service file
            servicefile_path = os.path.dirname(servicefile_w_path)

            updated_service_contents_str = convert_local_files(service_name,
                                                  service_contents_str,
                                                  servicefile_path,
                                                  challenge)

            # set the service in the registry
            set_remote_string_w_challenge(reg_key, updated_service_contents_str, challenge)

    else:
        err = "service path %s doesn't exist"%servicefile_path

    return err

# a service name is considered complete if it includes a version tag
def is_service_name_complete(service_name):

    is_complete = False

    name_parts = service_name.split(':')

    if len(name_parts)==2:

        # a tag is included, so name is complete
        is_complete = True

    return is_complete

# if only know partial service name (no label), returns true
# if the complete version of the service is in registry
def is_service_available_partial_name(service_partial_name):

    is_available = False

    if not is_service_name_complete(service_partial_name):
        # see if a service with tag=latest is available in the registry
        complete_name_candidate = '%s:%s'%(service_partial_name,"latest")
        service = get_service_by_name(complete_name_candidate)

        if service:
            is_available = True

    return is_available

def get_complete_name(service_name):

    complete_name = ""

    if not is_service_name_complete(service_name):
        # see if a service with tag=latest is available in the registry
        complete_name_candidate = '%s:%s'%(service_name,"latest")
        service = get_service_by_name(complete_name_candidate)

        if service:
            complete_name = complete_name_candidate

    return complete_name

YAC_SERVICE_SUFFIX="-service"

def get_all_service_names(search_str=""):

    service_names = []
    all_service_name = []

    # get all registry keys
    registry_keys = get_registry_keys()

    # find all keys with _naming suffix
    for key in registry_keys:

        print("key: %s, type: %s"%(key, type(key)))
        if key.endswith(YAC_SERVICE_SUFFIX) and (not search_str or search_str in key):
            # remove the suffix and append to list
            service_names = service_names + [key.replace(YAC_SERVICE_SUFFIX,'')]
        elif key.endswith(YAC_SERVICE_SUFFIX):
            all_service_name.append(key.replace(YAC_SERVICE_SUFFIX,''))

    if service_names:
        return service_names
    else:
        return all_service_name
