#!/usr/bin/env python

import sys, os
from yac.lib.search import search
from yac.lib.schema import validate
from yac.lib.engines import load_artifact_obj


class Artifacts():

    def __init__(self,
                 serialized_artifacts):

        validate(serialized_artifacts, "yac/schema/artifacts.json")

        self.artifacts = []

        for serialized_artifact in serialized_artifacts:

            artifact_type = serialized_artifact['type']

            artifact_obj, err = load_artifact_obj(artifact_type,
                                                  serialized_artifact)

            if not err:
                self.artifacts.append( artifact_obj )
            else:
                print("artifact class for type '%s' not available. err: %s ... exiting"%(artifact_type,err))
                exit(1)


    def add(self, artifact):

        self.artifacts = self.artifacts + artifact.artifacts

    def make(self,
             params,
             vaults,
             artifact_name="",
             dry_run_bool=False):

        err = ""

        for artifact in self.artifacts:

            if (not artifact_name or
                artifact_name == artifact.get_name()):

                err = artifact.make(params,
                                    vaults,
                                    dry_run_bool)

                if err:
                    # break out of the make loop upon first failure
                    break

        return err

    def get_all(self):
        return artifacts

    def get_names(self):

        names = []

        for artifact in self.artifacts:

            names.append(artifact.get_name())

        return names

    def get(self,
            artifact_name):

        for artifact in self.artifacts:

            if artifact.get_name() == artifact_name:

                return artifact

        return None


    def pprint(self):

        ret = ""
        for artifact in self.artifacts:

            ret = ret + "name: %s\ndescription: %s\n\n"%(artifact.get_name(),
                                                         artifact.get_description())

        return ret

    def __str__(self):

        ret = ""
        for artifact in self.artifacts:

            ret = ret + "%s\n"%(str(artifact))

        return ret



