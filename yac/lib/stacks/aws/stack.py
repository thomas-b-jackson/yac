import os, json, urllib.parse, boto3, subprocess
import shutil, jmespath, sys, time, imp
import datetime as dt
from botocore.exceptions import ClientError
from yac.lib.file import dump_file_contents
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.naming import get_stack_name
from yac.lib.file import get_localized_script_path, dump_dictionary
from yac.lib.file import FileError, file_in_registry, get_file_contents
from yac.lib.file import localize_file, get_dump_path
from yac.lib.file import get_file_contents
from yac.lib.template import apply_templates_in_file, apply_templates_in_dir
from yac.lib.search import search
from yac.lib.module import get_module
from yac.lib.schema import validate
from yac.lib.params import Params
from yac.lib.stacks.aws.session import get_session
from yac.lib.stacks.aws.session import ASSUME_ROLE_KEY
from yac.lib.stacks.aws.paths import get_credentials_path
from yac.lib.stacks.aws.credentials import create_role_config
from yac.lib.stacks.stack import Stack

UPDATING = "Updating"
BUILDING = "Building"

STACK_STATES = ['CREATE_IN_PROGRESS', 'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_IN_PROGRESS',
                'ROLLBACK_FAILED','ROLLBACK_COMPLETE','DELETE_IN_PROGRESS','DELETE_FAILED',
                'DELETE_COMPLETE','UPDATE_IN_PROGRESS','UPDATE_COMPLETE_CLEANUP_IN_PROGRESS',
                'UPDATE_COMPLETE','UPDATE_ROLLBACK_IN_PROGRESS','UPDATE_ROLLBACK_FAILED',
                'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS','UPDATE_ROLLBACK_COMPLETE']

CREATE_IN_PROGRESS_STATE = 'CREATE_IN_PROGRESS'
NEWLY_CREATED_STATE = 'CREATE_COMPLETE'

UNKNOWN_STATE = "unknown"

NON_EXISTANT = "non-existant"

NEWLY_CREATED_STATE = 'CREATE_COMPLETE'

UPDATE_COMPLETE_STATE = 'UPDATE_COMPLETE'
UPDATE_COMPLETE_STATES = ['UPDATE_COMPLETE','UPDATE_ROLLBACK_COMPLETE']

UPDATE_IN_PROGRESS_STATE = 'UPDATE_IN_PROGRESS'

UPDATABLE_STATES = ['CREATE_COMPLETE','UPDATE_COMPLETE','UPDATE_ROLLBACK_COMPLETE']

UNKNOWN_STATE = "unknown"

MAX_TEMPLATE_LEN = 51200

# an aws cloud formation stack
class AWSStack(Stack):

    def __init__(self,
                 serialized_stack):

        self.type = "aws-cloudformation"

        # validate. this should raise an error if required
        # fields aren't present
        validate(serialized_stack, "yac/schema/stacks/aws/stack.json")

        self.parameters = search("Parameters",serialized_stack,{})
        self.resources = search("Resources",serialized_stack, {})
        self.conditions = search("Conditions",serialized_stack, {})

        # for mapping cloud formation parameters to yac params
        self.cf_param_map = ParameterMapping(search("ParameterMapping",
                                                serialized_stack, {}))

        self.boot_files = BootFiles(search('"BootFiles"',
                              serialized_stack,{}))

    def add(self, stack):

        if (stack.impl and
            stack.impl.type == "aws-cloudformation"):

            self.parameters.update(stack.impl.parameters)
            self.resources.update(stack.impl.resources)
            self.conditions.update(stack.impl.conditions)
            self.cf_param_map.add(stack.impl.cf_param_map)

            self.boot_files.add(stack.impl.boot_files)

    def exists(self):

        client = self.session.client('cloudformation')

        try:
            response = client.describe_stacks(StackName=self.name)
            stack_count = len(response['Stacks'])
            return stack_count>0
        except:
            return False

    def build(self,
              params,
              deploy_mode_bool=False,
              context=""):

        self.params = params

        pipeline_run = params.get('pipeline-run', False)

        # initialize a session with boto3
        self.session,err = get_session(params)

        self.name = get_stack_name(self.params)

        # deploy any boot files specified by the service
        self.boot_files.deploy(self.params,
                               context,
                               dry_run_bool=False)

        # apply intrinsics to the stack template
        rendered_stack_template = apply_intrinsics(self.serialize(),
                                               self.params)

        stack_exits_bool = self.exists()

        # make sure stack is in an actionable state before proceeding
        stack_actionable,err = self.is_actionable()

        # if the stack does not yet exist, or if the stack exists and is in
        # an actionable state ...
        if (stack_exits_bool == False or stack_actionable):

            service_name = self.params.get('service-name')
            service_alias = self.params.get('service-alias')

            # determine if we are building or updating this stack
            action = UPDATING if stack_exits_bool else BUILDING

            # show build plan via stdout
            print("%s the %s service aliased as '%s'"%(action,
                                                       service_name,
                                                       service_alias))
            print("Service stack will be named: %s"%(self.name))

            if pipeline_run is True:
                # give user chance to bail
                print("Hit <enter> to continue..." )

            # get stack parameters
            stack_params = self.cf_param_map.get_params_array(self.params,
                                                              self.session,
                                                              self.name)

            # Get the optional "staging" location where the stack template can be staged.
            # The location is only used if the template string exceeds Amazon API's character limit.
            template_staging_path = self.params.get('template-staging-s3-path', "")

            # dump stack template to a string
            stack_template_str = json.dumps(rendered_stack_template)

            if action == BUILDING:

                response,err  = self.create_stack(template_string = stack_template_str,
                                                  stack_params    = stack_params,
                                                  template_staging_path = template_staging_path)

                if not err:
                    print('Stack creation in progress - use AWS console to watch construction and/or see errors')

            else:
                response,err = self.update_stack(template_string = stack_template_str,
                                                 stack_params    = stack_params,
                                                 template_staging_path = template_staging_path)

                if not err:
                    print('Stack update in progress - use AWS console to watch updates and/or see errors')

            # if this build is happening in the context of a deploy
            if deploy_mode_bool:

                # wait for stack update to complete
                self.wait()

        # return any errors
        return err

    def is_actionable(self):

        actionable = True
        err = ""

        stack_state = self.get_stack_state()

        # stack must have defined resource to be actionable
        if not self.resources:
            actionable = False
            err = "stack has no defined resources"

        elif stack_state == UNKNOWN_STATE:
            actionable = False
            err = "stack is in an unknown state"

        elif stack_state not in UPDATABLE_STATES:
            actionable = False
            err = "stack is not updatable. current state is: %s"%stack_state

        return actionable,err

    def serialize(self):

        return {
            "Parameters": self.parameters,
            "Resources":  self.resources,
            "Conditions": self.conditions
        }

    def __str__(self):

        return json.dumps(self.serialize(),indent=2)

    def delete(self,params):

        self.name = get_stack_name(params)

        print("Deletion of aws stacks not supported from the yac cli.")
        print("Use the aws cloudformation console instead, via stack: %s"%self.name)

    # block until stack update completes
    def wait(self):

        err = ""
        waiter = None
        client = self.session.client('cloudformation')

        if (self.exists() and
            self.get_stack_state() == UPDATE_IN_PROGRESS_STATE ):

            waiter = client.get_waiter('stack_update_complete')
            print("waiting for stack update to complete ...")

        elif (self.exists() and
              self.get_stack_state() == CREATE_IN_PROGRESS_STATE ):

            waiter = client.get_waiter('stack_create_complete')
            print("waiting for stack creation to complete ...")

        if waiter:

            # wait 30 seconds between status checks, and give up after
            # 60 attempts (i.e. 30 minutes)
            # an error is returned after max attempts has been exceeded
            err = waiter.wait(
                StackName=self.name,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 60
                })

            # verify stack is in the update complete state
            if not err:
                stack_state = self.get_stack_state()

                if stack_state not in UPDATABLE_STATES:
                    err = "aborting: stack is not ready"

        return err

    def dryrun(self,
               params,
               deploy_mode_bool=False,
               context=""):

        self.params = params

        # initialize a session with boto3
        self.session,err = get_session(params)

        self.name = get_stack_name(self.params)

        # deploy any boot files specified by the service
        self.boot_files.deploy(self.params,
                               context,
                               dry_run_bool=True)

        # apply intrinsics to the stack template
        rendered_stack_template = apply_intrinsics(self.serialize(),
                                                   self.params)

        stack_exits_bool = self.exists()

        # determine if we are building or updating this stack
        action = UPDATING if stack_exits_bool else BUILDING

        stack_state = self.get_stack_state()

        service_name = self.params.get('service-name')
        service_alias = self.params.get('service-alias')
        servicefile_path = self.params.get('servicefile-path')

        print("%s (dry-run) the %s service aliased as '%s'"%(action,
                                                             service_name,
                                                             service_alias))
        print("Stack state is currently: %s."%stack_state)
        print("Service stack will be named: %s"%self.name)

        # show the rendered templates
        self.show_rendered_templates(rendered_stack_template,
                                     deploy_mode_bool,
                                     service_alias)

        stack_params = self.cf_param_map.get_params_array(self.params,
                                                          self.session,
                                                          self.name)

        if stack_params:
            print("Param mapping:\n%s"%stack_params)
            print("Sanity check the params above.")

    def show_rendered_templates(self,
                                rendered_stack_template,
                                deploy_mode_bool,
                                service_alias):

        if rendered_stack_template:

            print_template = 'y'

            if not deploy_mode_bool:

                print_template = input("Print stack templates to stdout? (y/n)> ")

            if print_template and print_template=='y':

                # pretty-print rendered resources
                print(json.dumps(rendered_stack_template,indent=2))

            # dump template to a file
            cf_file_path = dump_dictionary(rendered_stack_template,
                           service_alias,
                           "cf.json")

            print("See stack template dumped to: %s"%cf_file_path)

    def changes(self,
                params,
                context):

        self.params = params

        # initialize a session with boto3
        self.session,err = get_session(self.params)

        self.name = get_stack_name(self.params)

        # apply intrinsics to the stack template
        rendered_stack_template = apply_intrinsics(self.serialize(),
                                               self.params)

        stack_exits_bool = self.exists()

        # determine if we are building or updating this stack
        action = UPDATING if stack_exits_bool else BUILDING

        stack_state = self.get_stack_state()

        # print stack template to a string
        stack_template_str = json.dumps(rendered_stack_template)

        service_name = self.params.get('service-name')
        service_alias = self.params.get('service-alias')

        if action == UPDATING:

            analyze_changes = input("(BETA!) Analyze changes associated with this stack update? (y/n)> ")

            if analyze_changes and analyze_changes=='y':

                # get stack params
                stack_params = self.cf_param_map.get_params_array(self.params,
                                                                  self.session,
                                                                  self.name, True)

                # Get the optional "staging" location where the stack template can be staged.
                # The location is only used if the template string exceeds Amazon API's character limit.
                template_staging_path = self.params.get('template-staging-s3-path', "")

                change_arn, change_error = self.analyze_changes(
                                                template_string = stack_template_str,
                                                stack_params    = stack_params,
                                                template_staging_path = template_staging_path)

                if not change_error:
                    print("Changes associated with this update can be viewed via the cloudformation console")
                    print("See the 'proposed-changes' change set via the 'Change Sets' tab on the %s stack"%self.name)
                else:
                    print("Change set creation failed with error: %s"%change_error)

    def cost(self,
             params,
             context):

        self.params = params

        # initialize a session with boto3
        self.session,err = get_session(params)

        self.name = get_stack_name(self.params)

        # apply intrinsics to the stack template
        rendered_stack_template = apply_intrinsics(self.serialize(),
                                               self.params)

        stack_exits_bool = self.exists()

        # determine if we are building or updating this stack
        action = UPDATING if stack_exits_bool else BUILDING

        stack_state = self.get_stack_state()

        # print stack template to a string
        stack_template_str = json.dumps(rendered_stack_template)

        service_name = self.params.get('service-name')
        service_alias = self.params.get('service-alias')

        estimate_cost = input("Estimate cost associate with stack resources? (y/n)> ")

        if estimate_cost and estimate_cost=='y':

            # get stack params
            stack_params = self.cf_param_map.get_params_array(self.params,
                                                              self.session,
                                                              self.name, True)

            # Get the optional "staging" location where the stack template can be staged.
            # The location is only used if the template string exceeds Amazon API's character limit.
            template_staging_path = self.params.get('template-staging-s3-path', "")

            cost_response, cost_error = self.cost_stack(
                                            template_string = stack_template_str,
                                            stack_params    = stack_params,
                                            template_staging_path = template_staging_path)

            if not cost_error:
                print("Cost of the resources for this service can be viewed here: %s"%(cost_response))
            else:
                print("Costing failed: %s"%cost_error)

    def get_stack_state( self ):

        client = self.session.client('cloudformation')

        if self.exists():

            response = client.describe_stacks(StackName=self.name)

            states = jmespath.search("Stacks[*].StackStatus",response)

            if len(states) == 1:
                state = states[0]
            else:
                state = UNKNOWN

        else:
            state = NON_EXISTANT

        return state

    # estimate cost of a stack
    def cost_stack( self,
                    template_string="",
                    stack_params = None ,
                    template_staging_path = None):

        cost_response = ""
        cost_error = ""

        client = self.session.client('cloudformation')

        try:

            if (len(template_string) > MAX_TEMPLATE_LEN and
                template_staging_path):

                # upload the template to the s3 location specified
                template_url = self.upload_template_to_s3(template_string, template_staging_path)

                response = client.estimate_template_cost(TemplateURL = template_url,
                                                         Parameters = stack_params)

                cost_response = str(response['Url'])

            elif (len(template_string) > MAX_TEMPLATE_LEN and
                not template_staging_path):

                cost_error =  ("Cost can't be calculated because the template string exceeds Amazon's character limit." +
                       "\nTo resolve, specify an S3 path to stage the template using the 'template-staging-s3-path' parameter.")

            else:
                response = client.estimate_template_cost(TemplateBody=template_string,
                                                         Parameters = stack_params)

                cost_response = str(response['Url'])

        except ClientError as e:

            cost_error = 'Stack costing failed: %s'%str(e)

        return cost_response, cost_error

    # analyze what is changing in a stack
    def analyze_changes( self,
                    template_string="",
                    stack_params = None ,
                    template_staging_path = None):

        change_set_id = ""
        change_error = ""

        client = self.session.client('cloudformation')

        try:

            if (len(template_string) > MAX_TEMPLATE_LEN and
                template_staging_path):

                # upload the template to the s3 location specified
                template_url = self.upload_template_to_s3(template_string, template_staging_path)

                response = client.create_change_set(TemplateURL = template_url,
                                                    Parameters = stack_params,
                                                    StackName = self.name,
                                                    ChangeSetName = "proposed-changes",
                                                    Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'])

                change_set_id = str(response['Id'])

            elif (len(template_string) > MAX_TEMPLATE_LEN and
                not template_staging_path):

                change_error =  ("Cost can't be calculated because the template string exceeds Amazon's character limit." +
                       "\nTo resolve, specify an S3 path to stage the template using the 'template-staging-s3-path' parameter.")

            else:
                response = client.create_change_set(TemplateBody=template_string,
                                                    Parameters = stack_params,
                                                    StackName = self.name,
                                                    ChangeSetName = "proposed-changes",
                                                    Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'])

                change_set_id = str(response['Id'])

        except ClientError as e:

            change_error = 'Stack change analysis failed with error: %s'%str(e)

        return change_set_id, change_error

    def create_stack(self,
                     template_string="",
                     stack_params=[],
                     template_staging_path=None,
                     stack_tags=[]):

        create_response = ""
        create_error = ""

        client = self.session.client('cloudformation')

        try:

            if (len(template_string) > MAX_TEMPLATE_LEN and
               template_staging_path):

                # upload the template to the s3 location specified
                template_url = self.upload_template_to_s3(template_string, template_staging_path)

                response = client.create_stack(StackName=self.name,
                                               TemplateURL=template_url,
                                               Parameters=stack_params,
                                               Tags=stack_tags,
                                               Capabilities=['CAPABILITY_IAM','CAPABILITY_NAMED_IAM'])

                create_response = str(response['StackId'])

            elif (len(template_string) > MAX_TEMPLATE_LEN and
                  not template_staging_path):

                create_error = ("Cost can't be calculated because the template string exceeds Amazon's character limit." +
                                "\nTo resolve, specify an S3 path to stage the template using the 'template-staging-s3-path' parameter.")

            else:
                response = client.create_stack(StackName=self.name,
                                               TemplateBody=template_string,
                                               Parameters=stack_params,
                                               Tags=stack_tags,
                                               Capabilities=['CAPABILITY_IAM',
                                                             'CAPABILITY_NAMED_IAM'])

                create_response = str(response['StackId'])

        except ClientError as e:

            create_error = 'Stack creation failed: %s'%str(e)

        return create_response, create_error

    def update_stack( self,
                      template_string="",
                      stack_params = [],
                      template_staging_path=None,
                      stack_tags = []):

        update_response = ""
        update_error = ""

        client = self.session.client('cloudformation')

        try:

            if (len(template_string) > MAX_TEMPLATE_LEN and
                template_staging_path):

                # upload the template to the s3 location specified
                template_url = self.upload_template_to_s3(template_string, template_staging_path)

                print("updating stack ...")
                response = client.update_stack(StackName=self.name,
                                               TemplateURL=template_url,
                                               Parameters = stack_params,
                                               Capabilities=['CAPABILITY_IAM',
                                                             'CAPABILITY_NAMED_IAM'])

                update_response = str(response['StackId'])

            elif (len(template_string) > MAX_TEMPLATE_LEN and
                not template_staging_path):

                create_error =  ("Cost can't be calculated because the template string exceeds Amazon's character limit." +
                       "\nTo resolve, specify an S3 path to stage the template using the 'template-staging-s3-path' parameter.")

            else:
                response = client.update_stack(StackName=self.name,
                                               TemplateBody=template_string,
                                               Parameters = stack_params,
                                               Capabilities=['CAPABILITY_IAM',
                                                             'CAPABILITY_NAMED_IAM'])

                update_response = str(response['StackId'])

        except ClientError as e:

            # we care about all errors exept those resulting from a no-op update
            if "No updates are to be performed" not in str(e):
                update_error = 'Stack creation failed: %s'%str(e)

        return update_response, update_error

    def cp_file_to_s3(self, source_file, destination_s3_url):
       # cp a file to an s3 bucket

        # make sure source file exists
        if os.path.exists(source_file):

            # push the vault dictionary to s3
            s3 = self.session.resource('s3')

            # separate s3 bucket and path from url
            destination_parts = destination_s3_url.split("/")
            if len(destination_parts)>=4:
                s3_bucket = destination_parts[2]
                s3_path = "/".join(destination_parts[3:])

                # uploading contents to s3
                s3.meta.client.upload_file(source_file,
                                           s3_bucket,
                                           s3_path)
            else:
                raise FileError("Destination must be an s3 url (e.g. s3://<bucket>/<path>/<file>)")

        else:
            raise FileError("Source file %s does not exist"%source_file)

    def upload_template_to_s3(self,template_string, template_staging_path):

        # dump the file to a tmp location
        file_path = dump_file_contents(template_string, 'staging', "cf.json")

        # copy the file to s3
        self.cp_file_to_s3( file_path, "s3://%s"%template_staging_path)

        return "https://s3.amazonaws.com/%s"%template_staging_path

class ParameterMapping():

    """ maps yac params into cloud formation parameters

    Args:
        serialized_param_map: dictionary satisfying ParameterMapping stanza in
                              yac/schema/stacks/aws.json
    Returns:
        An instance

    Raises:
        None

    """

    def __init__(self,
                 serialized_param_map):

        self.map = serialized_param_map

    def add(self, param_map_obj):

        self.map.update(param_map_obj.map)

    def get_params_array(self,
                         params,
                         session,
                         stack_name,
                         costing=False):

        # returns a boto3.cloudformation-appropriate parameter array

        stack_parameters = []
        self.session = session
        self.params = params

        # apply intrinsics in the map
        rendered_map = apply_intrinsics(self.map,self.params)

        if rendered_map:

            # get the state of the stack
            stack_exists = self.stack_exists(stack_name)

            for cf_param_key in list(rendered_map.keys()):

                # is this cloud formation parameter immutable?
                cf_param_immutable = ("immutable" in rendered_map[cf_param_key] and
                                rendered_map[cf_param_key]["immutable"])

                # if either:
                #   1) params are being using for costing (not actual printing), or
                #   2) the stack does not yet exist, or
                #   3) the stacks exists AND the cf parameter is NOT immutable AND ...
                #           the param setpoint has changed, then
                #
                # provide a value via ParameterValue
                #
                # otherwise, use previous value

                # note: condition 1) is to workaround a bug where the costing api can't
                # handle the UsePreviousValue flag

                # get the yac param value for this cf parameter
                yac_param_value = ""
                if "value" in rendered_map[cf_param_key]:
                    yac_param_value = rendered_map[cf_param_key]['value']

                # if the stack exists and the parameter is not immutable, the cf parameter
                # can be changed, so we need to figure out what it currently is
                if stack_exists and not cf_param_immutable:
                    # get the parameter value as it is currently set in the stack itself
                    stack_setpoint = self.get_stack_param_value( cf_param_key )

                if ( costing or
                     not stack_exists or
                     (stack_exists and not cf_param_immutable and
                        yac_param_value != stack_setpoint) ):

                    stack_parameters.append({"ParameterKey": cf_param_key,
                                            "ParameterValue": yac_param_value})
                else:
                    # use previous value
                    stack_parameters.append({"ParameterKey": cf_param_key,
                                            "UsePreviousValue": True })

        return stack_parameters

    def get_stack_param_value( self , stack_param_name ):

        value = ""

        client = self.session.client('cloudformation')

        response = client.describe_stacks(StackName=self.name)

        if response['Stacks']:
            stack = response['Stacks'][0]
        else:
            stack = {}

        if (stack and 'Parameters' in stack):
            for param in stack['Parameters']:
                if param['ParameterKey'] == stack_param_name:
                    value = param['ParameterValue']

        return value

    def stack_exists(self, stack_name):

        client = self.session.client('cloudformation')

        try:
            response = client.describe_stacks(StackName=stack_name)
            stack_count = len(response['Stacks'])
            return stack_count>0
        except:
            return False

class BootFiles():

    """ Boot files are typically configuration files that a service needs on its
           EC2 host at boot time.
        The deploy() method copies files and/or directories of files to S3.
        The UserData portion of an EC2 must then provide the code to copy them
           down from S3 and into place on the EC2 filesystem.
    Args:
        serialized_boot_files: dictionary satisfying BootFiles stanza in
                               yac/schema/stacks/aws.json
        params:  a Params instance

    Returns:
        A instance

    Raises:
        None

    """

    def __init__(self,
                 serialized_boot_files):

        # first validate. this should throw an exception if
        # required fields aren't present
        # validate(serialized_boot_files, "yac/schema/boot_files.json")

        self.files = search("files",serialized_boot_files,[])
        self.directories = search("directories",serialized_boot_files,[])

    def add(self, boot_files_obj):

        self.files = self.files + boot_files_obj.files

        self.directories = self.directories + boot_files_obj.directories

    def deploy(self, params, context, dry_run_bool=False):

        """ Deploy boot files from source to destination.

        Args:
            dry_run_bool: deploy in dry-run mode

        Returns:
            None

        Raises:
            FileError: if something goes wrong
            TemplateError: it rendering template variables fails

        """

        # retain params
        self.params = params

        # get the path that rendered boot files will be staged
        dump_path = get_dump_path(self.params.get("service-alias"))

        # make sure path is empty
        if os.path.exists(dump_path):
            shutil.rmtree(dump_path)

        # render service parmeters in the files then deploy 'em
        # to destination
        self._deploy_files(context, dry_run_bool)

        # render service parmeters in the files contained in a set of
        # directories then deploy the directory structure to destination
        self._deploy_dirs(context, dry_run_bool)

    # Render service parmeters into file body, then load files to destination
    # Note: only s3 destinations are currently supported.
    def _deploy_files(self, context, dry_run_bool):

        servicefile_path = self.params.get("servicefile-path")
        dump_path = get_dump_path(self.params.get("service-alias"))

        session,err = get_session(self.params)

        for this_file in self.files:

            if 'file-params' in this_file:

                file_params = Params(this_file['file-params'])

                # combine file params with the other params
                self.params.add(file_params)

            # render templates in the serialized file descriptor
            rendered_boot_file = apply_intrinsics(this_file,
                                                  self.params)

            # if necessary, localize file
            localized_file = localize_file(rendered_boot_file['src'],
                                           servicefile_path)

            if os.path.exists(localized_file):

                # replace any service parmeters variables in the file body and
                # return the name+path of the "rendered" file
                rendered_file = apply_templates_in_file(localized_file,
                                                        self.params,
                                                        dump_path)

                # if destination is s3 bucket and this is not a dry run
                if (self._is_s3_destination(rendered_boot_file['dest']) and
                    rendered_file):

                    # copy rendered file to s3 destination
                    self.cp_file_to_s3( session,
                                        rendered_file,
                                        rendered_boot_file['dest'],
                                        dry_run_bool)

                # if destination is another local file (mostly used for testing)
                elif not dry_run_bool:

                    # make sure destination directory exists
                    if not os.path.exists(os.path.dirname(rendered_boot_file['dest'])):
                        os.makedirs(os.path.dirname(rendered_boot_file['dest']))

                    # copy rendered file to the destination
                    shutil.copy(rendered_file,rendered_boot_file['dest'])

            else:

                error_msg = ("%s file deploy was not performed."%localized_file +
                             " Source file is missing")
                raise FileError( error_msg )

        if self.files and dry_run_bool:

            print("Rendered boot files can be viewed under: %s"%(dump_path))

    def cp_file_to_s3(self, session, source_file, destination_s3_url, dry_run_bool):
       # cp a file to an s3 bucket

        # make sure source file exists
        if os.path.exists(source_file):

            # push the vault dictionary to s3
            s3 = session.resource('s3')

            # separate s3 bucket and path from url
            destination_parts = destination_s3_url.split("/")
            if len(destination_parts)>=4:
                s3_bucket = destination_parts[2]
                s3_path = "/".join(destination_parts[3:])

                if not dry_run_bool:

                    # uploading contents to s3
                    s3.meta.client.upload_file(source_file,
                                               s3_bucket,
                                               s3_path)


                else:
                    self.show_differences(source_file,
                                              s3_bucket,
                                              s3_path,
                                              s3)


            else:
                raise FileError("Destination must be an s3 url (e.g. s3://<bucket>/<path>/<file>)")

        else:
            raise FileError("Source file %s does not exist"%source_file)


    def object_exists(self,s3_bucket,s3_path,s3):

        object_exists = False

        bucket = s3.Bucket(s3_bucket)
        objs = list(bucket.objects.filter(Prefix=s3_path))
        if len(objs) > 0 and objs[0].key == s3_path:
            object_exists = True

        return object_exists


    # Show differences length between s3 and local bootfiles
    def show_differences(self,
                         source_file,
                         s3_bucket,
                         s3_path,
                         s3):

        # Checking for existence in s3
        if not self.object_exists(s3_bucket,s3_path,s3):
            print("source file '%s' is new."%source_file)
        else:
            # Get size of file in s3
            s3_object = s3.meta.client.get_object(Bucket=s3_bucket, Key=s3_path)
            size_in_s3 = s3_object["ContentLength"]

            # Get size of file on source path
            local_size = os.path.getsize(source_file)
            # Uncoment below for debugging purposes
            # print "s3:%s, local:%s, filename:%s"%(size_in_s3, local_size, source_file)

            if size_in_s3 != local_size:
                print("source file '%s' is changing"%source_file)

    def _deploy_dirs(self, context, dry_run_bool):

        servicefile_path = self.params.get("servicefile-path")
        dump_path = get_dump_path(self.params.get("service-alias"))

        for this_idir in self.directories:

            # render intrinsics in the file dictionary
            this_dir = apply_intrinsics(this_idir, self.params)

            # render files under the dump path
            rendered_dir_path = os.path.join(dump_path,this_dir['src'])

            # render file variables in the source directory
            apply_templates_in_dir(this_dir['src'],
                                   self.params,
                                   rendered_dir_path,
                                   True)

            # if destination is s3 bucket
            if self._is_s3_destination(this_dir['dest']):

                # sync directories to s3 destination
                self.sync_dir_to_s3( context,
                                    rendered_dir_path,
                                    this_dir['dest'],
                                    dry_run_bool)

            # if destination is another local dir (mostly used for testing)
            elif not dry_run_bool:

                # clear destination dir if it exists
                if os.path.exists(this_dir['dest']):
                    shutil.rmtree(this_dir['dest'])

                # recursively copy files to local directory
                shutil.copytree(rendered_dir_path,this_dir['dest'])

        if self.directories and dry_run_bool:
            print("Rendered boot directory files can be viewed under: %s"%(rendered_dir_path))

   # returns true if file to be loaded is configured for an s3 destination
    def _is_s3_destination( self, destination ):

        s3_destination = False

        # S3 destinations are URL's with s3 as the scheme
        # Use this to detect an S3 destination

        # attempt to parse the destination as a URL
        url_parts = urllib.parse.urlparse(destination)

        if (url_parts and url_parts.scheme and url_parts.scheme == 's3'):

            s3_destination = True

        return s3_destination

    # sync a directory to an s3 bucket
    # raises an Error if source dir does not exists
    # or if s3 sync fails
    def sync_dir_to_s3(self,
                       context,
                       source_dir,
                       destination_s3_url,
                       dry_run_bool):

        # make sure source file exists
        if os.path.exists(source_dir):

            # form aws sync command for this directory
            # use --delete option to remove any files or directories already in s3
            # destination that aren't in source_dir
            # debug option is used to pass directory changes on dryrun

            dry_run_arg="--dryrun " if dry_run_bool else ""

            # the context arg is used to direct the aws cli to the
            # correct credential and/or iam role
            profile_arg=self.get_profile_arg(context)

            aws_cmd = "aws s3 sync %s %s %s %s %s--debug"%( source_dir,
                                                     destination_s3_url,
                                                     "--delete",
                                                     profile_arg,
                                                     dry_run_arg)
            try:
                aws_cmd_array = aws_cmd.split(" ")
                p = subprocess.Popen(aws_cmd_array,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    bufsize=1)
                for line_bytes in iter(p.stdout.readline, b''):
                    line = line_bytes.decode("utf-8")
                    if "size_changed: True" in line or "file does not exist at destination" in line:
                        if dry_run_bool:
                            print("Directory source file changing")
                            print(line, end=' ')
                p.stdout.close()
                p.wait()
            except subprocess.CalledProcessError as e:
                raise FileError("Error copying directory to s3 destination: %s"%e)

        else:
            raise FileError("Source directory %s does not exist"%source_dir)

    # create an argument for the aws cli to point it to either:
    # 1) the correct profile in a credentials file, or
    # 2) the correct iam role to assume
    # note: logic here should mirror the logic in get_session() in sessions.py
    def get_profile_arg(self,profile):

        # if running in desktop mode, the context arg for the
        # aws cli is --profile=<profile_key>, where profile_key
        # is per the users credentials file
        if self.params.get("desktop") and not profile:
            # in yac-generated aws credentials files, the default profile
            # is "default"
            profile='default'

        elif not self.params.get("desktop"):
            # assume we are running on an ec2 instance where
            #   aws access permissions are granted by either:
            #  1) the IAM role of the ec2 instance, or
            #  2) an IAM role to assume
            assumed_role_arn = self.params.get(ASSUME_ROLE_KEY)

            if not assumed_role_arn:

                # 1) set the profile to an empty string
                #    to ensure that the default role is used
                profile=""

            else:
                # 2) assume a specific role
                # Do this by first creating a ~/.aws/config file where the aws cli
                #    expects to find the ARN of the role to assume.
                profile="builder_role"
                create_role_config(assumed_role_arn,
                                   profile)



        profile_arg = "--profile=%s"%profile

        return profile_arg