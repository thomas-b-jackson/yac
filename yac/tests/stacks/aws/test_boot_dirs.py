import unittest, os, random, shutil
from yac.lib.file import get_file_contents, FileError
from yac.lib.stacks.aws.stack import BootFiles
from yac.lib.stacks.aws.credentials import get_session
from yac.lib.params import Params
from yac.lib.intrinsic import IntrinsicsError
from yac.lib.template import TemplateError
from yac.lib.stacks.aws.session import ASSUME_ROLE_KEY

class TestCase(unittest.TestCase):

    def test_dirs(self):

        cwd = os.getcwd()
        temp_test_dir = "yac/tests/stacks/aws/vectors/deploy"
        svc_file_path = os.path.join(cwd,temp_test_dir)
        service_parmeters = {"render-me": {"value": "baby!"},
                             "service-alias": {"value": "testing"}}
        serialize_boot_files = {
            "directories": [
                {
                    "src":  "yac/tests/stacks/aws/vectors/deploy/sample_dir",
                    "dest": "/tmp/stacks/aws/vectors/deploy/rendered/sample_dir"
                }
                ]
            }

        boot_files = BootFiles(serialize_boot_files)

        deploy_success = True
        try:
            boot_files.deploy(Params(service_parmeters),
                                    context="",
                                    dry_run_bool=False)

        except TemplateError as e:
            print(e.msg)
            deploy_success = False

        except IntrinsicsError as ie:
            # this error will be thrown if any intrinsics couldn't
            # be rendered this
            print(ie.msg)
            deploy_success = False

        self.assertTrue(deploy_success)

    def test_dir_non_existent(self):

        cwd = os.getcwd()
        temp_test_dir = "yac/tests/stacks/aws/vectors/deploy"
        svc_file_path = os.path.join(cwd,temp_test_dir)
        service_parmeters = {"render-me": {"value": "baby!"},
                             "service-alias": {"value": "testing"}}
        serialize_boot_files = {
            "directories": [
                {
                    "src":  "i_do_not_exist",
                    "dest": "/tmp/stacks/aws/vectors/deploy/rendered/sample_dir"
                }
                ]
            }

        boot_files = BootFiles(serialize_boot_files)

        error_thrown = False
        try:
            boot_files.deploy(Params(service_parmeters),
                                   context="",
                                   dry_run_bool=False)

        except TemplateError as e:
            # this is the expected condition
            error_thrown = True

        self.assertTrue(error_thrown)
