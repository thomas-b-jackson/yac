import unittest, os, random, shutil
from yac.lib.file import get_file_contents, FileError
from yac.lib.stacks.aws.stack import BootFiles
from yac.lib.stacks.aws.credentials import get_session
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_files(self):

        temp_test_dir = "yac/tests/stacks/aws/vectors/deploy"
        service_parmeters = {"render-me": {"value": "baby!"},
                             "servicefile-path": {"value": temp_test_dir},
                             "service-alias": {"value": "testing"}}
        serialize_boot_files = {
            "files": [
            {
                "src":  "deploy_for_boot.txt",
                "dest": "/tmp/stacks/aws/vectors/deploy/rendered/deploy_for_boot.txt"
            }
            ]
        }

        boot_files = BootFiles(serialize_boot_files)

        try:
            boot_files.deploy(Params(service_parmeters),context="")

        except FileError as e:
            print(e.msg)

        # read file contents from destination file
        file_contents = get_file_contents(serialize_boot_files['files'][0]['dest'])

        # clean up
        shutil.rmtree("/tmp/stacks/aws/vectors/deploy/rendered")

        self.assertTrue(file_contents == "render my params, then deploy me %s"%(service_parmeters["render-me"]["value"]))

    def test_file_params(self):

        temp_test_dir = "yac/tests/stacks/aws/vectors/deploy"
        service_parmeters = {"render-me": {"value": "baby"},
                             "servicefile-path": {"value": temp_test_dir},
                             "service-alias": {"value": "testing"}}
        serialize_boot_files = {
            "files": [
                {
                    "src":  "deploy_for_boot_file_params.txt",
                    "dest": "/tmp/stacks/aws/vectors/deploy/rendered/deploy_one_way.txt",
                    "file-params": {
                        "also-render-me": {
                          "comment": "render first exclamation",
                          "value":   "oooh!"
                        }
                    }
                },
                {
                    "src":  "deploy_for_boot_file_params.txt",
                    "dest": "/tmp/stacks/aws/vectors/deploy/rendered/deploy_other_way.txt",
                    "file-params": {
                        "also-render-me": {
                          "comment": "render second exclamation",
                          "value":   "no!"
                        }
                    }
                }
                ]
            }

        boot_files = BootFiles(serialize_boot_files,
                               )

        try:
            boot_files.deploy(Params(service_parmeters),
                              context="")

        except FileError as e:
            print(e.msg)

        # read file contents from destination files
        file_contents1 = get_file_contents(serialize_boot_files['files'][0]['dest'])
        file_contents2 = get_file_contents(serialize_boot_files['files'][1]['dest'])

        # clean up
        shutil.rmtree("/tmp/stacks/aws/vectors/deploy/rendered")

        self.assertTrue(file_contents1 == "baby, %s, baby, %s"%("baby","oooh!"))
        self.assertTrue(file_contents2 == "baby, %s, baby, %s"%("baby","no!"))