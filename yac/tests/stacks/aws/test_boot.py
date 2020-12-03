import unittest, os, random
from yac.lib.stacks.aws.boot import do_calc
from yac.lib.file import register_file, clear_file_from_registry, get_file_reg_key
from yac.lib.registry import get_private_registry, set_private_registry, MOCK_REGISTRY_DESC
from yac.lib.params import Params

def string_in_list(test_list, test_string):
    in_list=False
    for item in test_list:
        if test_string in item:
            in_list = True
            break

    return in_list

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # save currently configured registry so it can be re-set at the
        # conclusion of testing
        cls.current_registry = get_private_registry()

        # set private registry to a mock registry
        set_private_registry(MOCK_REGISTRY_DESC)

    @classmethod
    def tearDownClass(cls):

        # re-set users private registry
        set_private_registry(cls.current_registry)

    # test that all of the lines gets returned, with a cr between lines
    def test_boot(self):

        # run test
        boot_list,err = do_calc(["yac/tests/stacks/aws/vectors/boot_simple.sh"],Params({}))

        len_check = len(boot_list)==20

        self.assertTrue(len_check)

     # test the parameter got rendered into the boot file
    def test_boot_param(self):

        test_parameters = {
            "param1" : {
              "type" : "string",
              "value": "http"
            },
            "param2" : {
              "type" : "string",
              "value": "xeno"
            }
        }

        # run test
        boot_list,err = do_calc(["yac/tests/stacks/aws/vectors/boot.sh"],
                            Params(test_parameters))

        # test that http got rendered in
        param_check1 = string_in_list(boot_list, "http")
        param_check2 = string_in_list(boot_list, "xeno")

        self.assertTrue(param_check1 and param_check1)

    # with boot file located in registry, test that all of the lines gets returned,
    # with a cr between lines
    def test_reg_boot(self):

        boot_file_path = "yac/tests/stacks/aws/vectors/boot_simple.sh"

        # create a random value to put into registry
        file_key = "test-key-" + str(random.randint(1, 1000))
        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))

        # register file
        register_file(file_key, boot_file_path, challenge_phrase)

        # get file url
        file_url = get_file_reg_key(file_key)

        # run test
        boot_list,err = do_calc([file_url],Params({}))

        # clean up - remove the test file from the registry
        clear_file_from_registry(file_key,challenge_phrase)

        len_check = len(boot_list)==20

        self.assertTrue(len_check)