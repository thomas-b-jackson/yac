#!/usr/bin/env python

import json, requests, os, getpass, getpass, subprocess, sys
import boto3, botocore, socket
import datetime as dt
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from yac.lib.search import search
from yac.lib.schema import validate
from yac.lib.params import Params
from yac.lib.stacks.aws.paths import get_credentials_path, get_configs_path
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.inputs import Inputs
from yac.lib.stacks.aws.session import get_session
# defaults urls
# note: these haven't changed for the last few years
TOKEN_ENDPOINT_URL = "https://pbcld-awsToken.nordstrom.net/authentication/awsToken"
ROLE_ENDPOINT_URL = "https://pbcld-awsToken.nordstrom.net/authentication/roleArns"

class NordstromAWSCredentialer():

    def __init__(self,
                 credentials_descriptor):

        """ Generates aws credentials for nordstrom users.

        Args:
            credentials_descriptor: A dictionary containing serialized credentialer,
                               satisfying the yac/schema/aws/credentialer.json schema

        Raises:
            ValidationError: if a inputs fails schema validation

        """

        validate(credentials_descriptor, "yac/schema/stacks/aws/credentialer.json")

        self.accounts = search("accounts",
                               credentials_descriptor,[])

        self.region = search("region", credentials_descriptor,[])

        # if urls not provided, use defaults
        self.token_endpoint_url = search('"token-endpoint-url"',
                                          credentials_descriptor,
                                          TOKEN_ENDPOINT_URL)

        self.role_endpoint_url = search('"role-endpoint-url"',
                                          credentials_descriptor,
                                          ROLE_ENDPOINT_URL)

        # initialize the inputs (for driving user prompts)
        self.inputs = Inputs(search("Inputs",
                                    credentials_descriptor,{}))

    def create(self,
               params,
               vaults,
               overwrite_bool):

        # Writes credentials to a file for each configured account
        #
        # returns:
        #   err: string containing error message for failures

        err = ""
        self.params = params

        # process creds-specific inputs and load results into params
        self.inputs.load(self.params)

        if not self.is_desktop():
            # if this is being run on a build server, aws access permissions should be
            # conferred via an iam role rather than via credentials
            print("aws credentials not created ... assuming access provided via iam role")
            print("(note: if running on desktop, indicate by exporting the env variable DESKTOP=true)")
            return err

        token_file_path = get_credentials_path()

        token_file_dir = os.path.dirname(token_file_path)

        # make sure directory exists
        if not os.path.exists(token_file_dir):
            os.makedirs(token_file_dir)

        # if the token file doesn't exist or has expired, or if
        # the file should be overwritten regardless of its status ...
        if overwrite_bool or self.needs_updating(token_file_path):

            # write credentials into file
            file_ = open( token_file_path, 'w')

            # accounts support instrinsics. render before proceeding
            accounts = apply_intrinsics(self.accounts,self.params)

            for account in accounts:

                account_name = account['name']

                # create access tokens via lan credentials
                aws_access,err = self.get_session_tokens(account_name)

                if not err:

                    print("generating credentials for aws account: %s"%account_name)

                    # note that the token is included twice due to an inconsistency in aws
                    # cli versus boto SDK.
                    # aws cli uses aws_session_token while boto uses aws_security_token
                    credentials = "aws_access_key_id = " + aws_access['AccessKey'] + "\n" + \
                                  "aws_secret_access_key = " + aws_access['SecretAccessKey'] + "\n" + \
                                  "aws_session_token = " + aws_access['SessionToken'] + "\n" + \
                                  "aws_security_token = " + aws_access['SessionToken'] + "\n\n"

                    if 'alias' in account:
                        file_.write("[%s]\n"%account['alias'] + credentials)
                        print("warning: the 'alias' in nordstrom aws credentials is deprecated. use 'profile' instead")
                    else:
                        file_.write("[%s]\n"%account['profile'] + credentials)

                    if account['default']:
                        file_.write("[default]\n" + credentials)

            file_.close()

        return err

    def get_session_tokens(self, account_name):
        # Creates a session token given an account
        #
        # args:
        #   account_name: aws account name
        #
        # files:
        #   .lanid: file containing lanid of aws user
        #   .lanpwd: file containin lanpwd of aws user
        #
        # returns:
        #    token: session token
        #    err: any erros encountered

        lanid = self.get_lan_id()
        pwd = self.get_lan_pwd()

        token = {}
        err = ""

        # get principal/role pair for the account input
        role,err = self.get_role(lanid, pwd, account_name)

        if not err:

            header = {}
            header['content-type'] = 'application/json'
            header['accept'] = 'application/json'

            lan_auth = "%s@nordstrom.net"%lanid

            # silence insecure request warnings
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

            response = requests.post(self.token_endpoint_url,
                                     auth=(lan_auth, pwd),
                                     headers=header,
                                     data=json.dumps(role),
                                     verify=False)

            if response.status_code == 200:

                token = response.json()

            else:
                err = "tokens not received!. Status: %s" %response.status_code

        return token,err

    def get_role(self, lanid, pwd, role_str):
        # Return role given a lanid and password and account
        #
        # returns:
        #   role: dictionary containing role
        #   err: string with any errors encountered

        role = {}
        err = ""

        header = {}
        header['content-type'] = 'application/json'
        header['accept'] = 'application/json'

        lan_auth = "%s@nordstrom.net"%lanid

        # silence insecure request warnings
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        response = requests.get(self.role_endpoint_url,
                                auth=(lan_auth, pwd),
                                verify=False)

        if response.status_code == 200:

            pairs = response.json()

            # find the non-prod pair
            for pair in pairs:

                if role_str in pair['Role']:

                    role = pair
        else:

            err = ("Could not retrieve aws accounts for " +
                   "user '%s'. "%lan_auth +
                   "Status code: %s\n"%response.status_code)

        return role,err

    def get_lan_pwd(self):

        lan_pwd=""

        # default location for lan pwd file
        pwd_cache_path = os.path.join(get_cache_path(),
                                               '.lanpwd')

        if  os.path.exists(pwd_cache_path):

            print("reading cached password from %s ..."%pwd_cache_path)

            with open(pwd_cache_path, 'r') as myfile:
                # read pwd from file and strip off any whitespace chars
                lan_pwd=myfile.read().strip()

        else:

            lan_pwd = getpass.getpass("Please input your lan pwd >> ")

            # cache the pwd for future use
            pwd_cache_dir = os.path.dirname(pwd_cache_path)

            # make sure directory exists
            if not os.path.exists(pwd_cache_dir):
                os.makedirs(pwd_cache_dir)

            with open(pwd_cache_path, 'w') as myfile:
                myfile.write(lan_pwd)

        return lan_pwd

    def get_lan_id(self, disallow_caching=False):

        lan_id=""

        # default location for lan is
        id_cache_path = os.path.join(get_cache_path(),
                                            '.lanid')

        if  os.path.exists(id_cache_path):
            with open(id_cache_path, 'r') as myfile:

                # strip any carriage returns
                lan_id=myfile.read().strip()
        else:

            lan_id=getpass.getuser()

        return lan_id

    def needs_updating(self, creds_file_path):
        # returns true if either:
        #   * the token file does not exist, or
        #   * the token file is empty, or
        #   * the token file is more than an hour old
        needs_updating=True

        if os.path.exists(creds_file_path):

            # make sure file isn't empty
            if os.stat(creds_file_path).st_size > 2:

                filetime = dt.datetime.fromtimestamp(os.path.getctime(creds_file_path))

                if (filetime.day == dt.datetime.now().day and
                    filetime.hour == dt.datetime.now().hour ):
                    # was created on this day in this hour, so
                    # does not need updating
                    print("aws credentials are still fresh so won't be updated ...")
                    needs_updating = False

            elif os.stat(creds_file_path).st_size <= 2:
                print("aws credentials is empty so will be updated ...")
                needs_updating = True

        return needs_updating

    def creds_exist(self):
        return os.path.exists(get_credentials_path())

    def is_desktop(self):

        # the desktop params is set to true if yac was run from a developer desktop
        return self.params.get('desktop')

def create_role_config(assumed_role_arn, profilename="arbitrary_name"):
    # create the ~/.aws/config file that is used on an ec2 instance when
    # you need that instance to assume a specified iam role (other than the
    # the one already assigned to the instance)
    #
    # args:
    #   assumed_role_arn: string containing arn of role to assume
    #   profilename: string containing name of the profile to associate with the arn
    # returns:
    #   string: name of the profile in the config file to use with aws cli operations

    # create a file formatted as:
    # [profile profilename]
    # role_arn = <rolearn>
    # credential_source = Ec2InstanceMetadata
    #
    # see also: https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-role.html

    config_file_path = get_configs_path()

    config_file_dir = os.path.dirname(config_file_path)

    # make sure directory exists
    if not os.path.exists(config_file_dir):
        os.makedirs(config_file_dir)

    print("generating config for assuming aws role: %s"%assumed_role_arn)

    # write profile name and role arn into file
    file_ = open( config_file_path, 'w')

    configs = "[profile %s]\n"%profilename + \
              "role_arn = %s\n"%assumed_role_arn + \
              "credential_source = Ec2InstanceMetadata\n\n"

    file_.write(configs)

    file_.close()

    return profilename

def get_cache_path():

    return os.path.join(os.path.expanduser("~"),
                                           ".yac",
                                           "credentials")