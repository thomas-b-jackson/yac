import os, json, re, boto3, subprocess, sys
import docker
from yac.lib.template import apply_templates_in_file, apply_templates_in_dir
from yac.lib.search import search
from yac.lib.schema import validate
from yac.lib.inputs import Inputs
from yac.lib.secrets import Secrets
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.paths import get_dump_path

# name of the host providing a docker api on port 80
BUILDER_HOST = "imagebuilder.nonprod.dots.vip.nordstrom.com"
BUILDER_PORT = 80
ARTIFACTORY_URL = "https://artifactory.nordstrom.com/artifactory"

class ContainerImage():

    # for building docker container images
    def __init__(self,
                 serialized_artifact):

        validate(serialized_artifact, "yac/schema/makers/container_image.json")

        self.name = search("name",serialized_artifact,"")
        self.description = search("description",serialized_artifact,"")

        self.image = search("image",serialized_artifact)

        # the registry where the images should be pushed
        # defaults to artifactory
        self.registry = search('registry',
                                serialized_artifact,
                                ARTIFACTORY_URL)

        # initialize the inputs (for driving user prompts)
        self.inputs = Inputs(search("Inputs",
                                    serialized_artifact,{}))

        self.secrets = Secrets(search('"Secrets"',
                                    serialized_artifact,{}))

        # client for most operations
        self.client = docker.DockerClient('tcp://%s:%s'%(BUILDER_HOST,
                                                         BUILDER_PORT))

        # client for "low-level" build operations (e.g. builds that send
        # the details on each layer built to stdout )
        # TODO: figure out why auth isn't working from inside a container
        # with this one
        self.api_client = docker.APIClient('tcp://%s:%s'%(BUILDER_HOST,
                                                         BUILDER_PORT))

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def make(self,
             params,
             vaults,
             dry_run_bool=False):

        self.params = params

        # process inputs and load results into params
        self.inputs.load(self.params)

        # load secrets into parmas
        self.secrets.load(self.params,
                          vaults)

        # build the image
        err = self.build(dry_run_bool)

        if not err:

            # login to container registry specified in the servicefile
            err = self.login()

            if not err:

                # push the image to the registry
                err = self.push(dry_run_bool)

        return err

    def login(self):

        err = ""
        # render intrinsics in the registry
        rendered_registry = apply_intrinsics(self.registry,
                                             self.params)
        try:

            print("login using api client")
            response = self.client.login(username = rendered_registry['username'],
                              password = rendered_registry['password'],
                              registry = rendered_registry['host'])

            print(response)

        except docker.errors.APIError as ae:
            err = ae

        return err

    def build(self,
              dry_run_bool=False):

        err = ""
        build_success = False

        # render intrinsics in the image
        rendered_image = apply_intrinsics(self.image,
                                          self.params)

        # put the rendered files in the std dump path so they
        #  can be viewed after the yac container stops
        dump_path = get_dump_path(params.get("service-alias"))
        build_path = os.path.join(dump_path,"docker")

        # path to the docker file (relative to servicefile)
        self.dockerfile_path = search('"dockerfile"',rendered_image,"")

        servicefile_path = self.params.get('servicefile-path')

        dockerfile_full_path = os.path.join(servicefile_path,self.dockerfile_path)

        if os.path.exists(dockerfile_full_path):

            # render variables in the docker file
            apply_templates_in_file(dockerfile_full_path,
                                    self.params,
                                    build_path)

            # assume files are in the same location as the dockerfile
            apply_templates_in_dir(os.path.dirname(dockerfile_full_path),
                                   self.params,
                                   build_path)

            self.image_name =  search("name",rendered_image,"")
            self.image_label = search("label",rendered_image,"")

            # build args
            self.build_args = search('"build-args"',rendered_image,[])

            if dry_run_bool:

                print("see rendered files under %s"%build_path)
                print("(dry-run) building image %s:%s ..."%(self.image_name,
                                                            self.image_label))

            else:
                try:

                    print("building image %s:%s ..."%(self.image_name,
                                                      self.image_label))
                    # build the image
                    self.image,log = self.client.images.build(tag="%s:%s"%(self.image_name,
                                                                   self.image_label),
                                                      path=build_path,
                                                      buildargs=self.build_args)

                    for line in log:

                        if 'stream' in line:
                            print(line['stream'])
                        else:
                            print(line)


                except docker.errors.APIError as ae:
                    err = "APIError: %s"%ae

                except docker.errors.BuildError as be:
                    err = "BuildError: %s"%be

                except TypeError as te:
                    err = "TypeError: %s"%te
        else:
            err = "dockerfile at %s does not exist"%dockerfile_full_path

        return err

    def push(self,
             dry_run_bool=False):

        if dry_run_bool:
            print("(dry-run) pushing image %s:%s ..."%(self.image_name,self.image_label))

        else:
            print("pushing image %s:%s ..."%(self.image_name,self.image_label))

            # push the image to registry
            response = self.client.images.push(repository=self.image_name,
                                               tag=self.image_label)

            print(response)

