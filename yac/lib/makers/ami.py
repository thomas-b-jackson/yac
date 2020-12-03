import os, json, re, boto3, subprocess, sys, jmespath
from yac.lib.template import apply_templates_in_dir
from yac.lib.search import search
from yac.lib.inputs import Inputs
from yac.lib.secrets import Secrets
from yac.lib.paths import get_dump_path
from yac.lib.schema import validate
from yac.lib.stacks.aws.session import get_session

class AMI():
    # for building AMIs (amazon machine images) using packer

    def __init__(self,
                 serialized_artifact):

        validate(serialized_artifact, "yac/schema/makers/ami.json")

        self.name = search('name', serialized_artifact)

        self.description = search('description', serialized_artifact)

        # the aws profile aliasing the account to build in
        self.profile = search('profile', serialized_artifact)

        # path to the packer file
        self.packer_file = search('"packer-file"', serialized_artifact)

        # directory containing files that should be included in the build
        self.packable_dir = search('"packer-dir"', serialized_artifact,"")

        self.secrets = Secrets(search('"Secrets"',
                                      serialized_artifact,{}))

        # initialize the inputs (for driving user prompts)
        self.inputs = Inputs(search("Inputs",
                                    serialized_artifact,{}))

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def make(self,
             params,
             vaults,
             dry_run_bool=False):

        err = ""

        self.params = params

        # process inputs and load results into params
        self.inputs.load(self.params)

        # load secrets into parmas
        self.secrets.load(self.params,
                     vaults)

        # if the packer dir wasn't specified, assume the same dir
        # that the packerfile is in
        self.set_packable_dir()

        # render variables in all files

        # put the rendered files in the std dump path so they
        #  can be viewed after the yac container stops
        dump_path = get_dump_path(params.get("service-alias"))

        build_path = os.path.join(dump_path,"packer")

        # print(self.params)

        apply_templates_in_dir(self.packable_dir,
                               self.params,
                               build_path)

        # from the packer build command
        packer_file_name = os.path.basename(self.packer_file)
        packer_cmd = "packer build %s"%(packer_file_name)

        if dry_run_bool:
            print("see rendered packer files under %s"%build_path)

        else:
            # the full file path to the gitlab.json file
            packer_path = os.path.join(build_path, packer_file_name)

            # get the AMI_Name && Override Parameter
            with open(packer_path, 'r') as f:
                packer_dict = json.load(f)

            ami_name = jmespath.search("builders[0].ami_name", packer_dict)
            override_param = jmespath.search("builders[0].force_deregister", packer_dict)

            if ( self.ami_exists(params,ami_name) and override_param is False):
                print("AMI already exists and packer file includes instructions to NOT overwrite")

            else:
                print("build command:\n{0}".format(packer_cmd))
                # get the current working dir
                curr_dir = os.getcwd()

                # cd to the tmp dir
                os.chdir(build_path)

                # the subprocess command expects the command to be split into an array
                # on whitespace boundaries.
                packer_cmd_array = packer_cmd.split(" ")

                try:

                    last_line = ""
                    process = subprocess.Popen(packer_cmd_array, stdout=subprocess.PIPE)
                    for c_bytes in iter(lambda: process.stdout.read(1), ''):

                        c = c_bytes.decode("utf-8")
                        process.poll()
                        # write this char to stdout
                        if c:
                            sys.stdout.write(c)

                            # troll for ami ids in the packer output by converting individual
                            # chars into packer output lines and using a regex to find ami ids
                            # in each line
                            if c != '\n':
                                last_line=last_line + c

                            else:
                                # cache ami info that appear for future reference
                                # in front end builds
                                ami_id = self._find_ami_id(last_line)

                                if ami_id:
                                    self.ami_id = ami_id

                                # reset the line
                                last_line=c

                        else:
                            err = process.returncode
                            break

                except Exception as e:

                    err = str(e)

                # cd back to the original dir
                os.chdir(curr_dir)

        return err

    # find ami id from a line of packer output
    def _find_ami_id(self,packer_output_str):

        ami_id = ""

        # use regex to look for the ami id in the packer output
        # second group matches any letter (case-insenstive) or int
        regex_result = re.search("(us-west-2: )(ami-[a-zA-Z0-9]{8,})",packer_output_str)

        # if it exists, second group holds the ami id
        if (regex_result and
            regex_result.group(2)):

            ami_id = regex_result.group(2)

        return ami_id

    def set_packable_dir(self):

        if not self.packable_dir:

            packer_file_full_path = os.path.join(self.params.get('servicefile-path'),
                                            self.packer_file)

            self.packable_dir = os.path.dirname(packer_file_full_path)

    def ami_exists(self,
                   params,
                   ami_name):

        ami_exists = False

        session, err = get_session(params)
        if not err:
            client = session.client('ec2')

            response = client.describe_images(
                Filters=[
                    {
                        'Name': 'name',
                        'Values': [ami_name]
                    }])
        else:
            return err


        if "Images" in response and len(response["Images"])==1:

            ami_exists = True

        return ami_exists
