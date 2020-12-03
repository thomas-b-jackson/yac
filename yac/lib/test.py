import os, datetime, jmespath, boto3, json
import kubernetes.client
import kubernetes.config
from kubernetes.client.rest import ApiException
from yac.lib.intrinsic import apply_custom_fxn
from yac.lib.file import localize_file, FileError
from yac.lib.drivers.artillery import ArtilleryDriver
from yac.lib.drivers.custom import CustomDriver
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.params import Params
from yac.lib.module import get_module
from yac.lib.schema import validate
from yac.lib.search import search

# Integrations tests, both functional and performance
class IntegrationTests():

    def __init__( self,
                  int_test_descriptor):

        # validate the test descriptor
        # note: this will raise an exception if validation fails
        validate( int_test_descriptor , "yac/schema/integration_tests.json")

        # raw because it my contain instrinsics
        self.raw_target_map = search('"target-map"',int_test_descriptor,{})

        self.results_store = search('"results-store"',int_test_descriptor,{})

        self.tests = search('tests',int_test_descriptor,[])

        self.test_groups = search('"test-groups"',int_test_descriptor,[])

        self.test_results = TestResults()


    def add(self,integration_tests):

        if integration_tests.tests:
            self.tests = self.tests + integration_tests.tests
        if integration_tests.test_groups:
            self.test_groups = self.test_groups + integration_tests.test_groups
        if integration_tests.raw_target_map:
            self.raw_target_map = integration_tests.raw_target_map

    def get_results(self):

        return self.test_results

    def get_tests(self):

        return self.tests

    def get_test_names(self):
        return search("[*].name",self.tests,[])

    def get_group_names(self):
        return search("[*].name",self.test_groups,[])

    def run(self,
            params,
            context="",
            test_names=[],
            group_names=[],
            setup_only=False,
            cleanup_only=False,
            test_only=False):
        # run tests
        #
        # args:
        #   params:       Params instance
        #   context:      string describing build context
        #   test_name:    run the tests with these test names
        #   group_name:   run the test groups with these group names
        #   setup_only:   boolean - perform setup only
        #   cleanup_only: boolean - perform cleanup only
        #   test_only:    boolean - skip setup and cleanup
        #
        # return:
        #   err: string with error message if setup or cleanup failed

        self.params = params

        # render intrinsics in tests
        rendered_tests = apply_intrinsics(self.tests, self.params)

        # render intrinsics in the target map
        self.target_map = apply_intrinsics(self.raw_target_map, self.params)

        tests_to_run,err = self._get_tests(test_names,
                                           rendered_tests)

        if not err:

            for test in tests_to_run:

                err = self._run_test( test,
                                    setup_only,
                                    cleanup_only,
                                    test_only,
                                    context )

        if not err:

            # render intrinsics in test groups
            rendered_test_groups = apply_intrinsics(self.test_groups, self.params)

            tests_groups_to_run,err = self._get_test_groups(group_names,
                                             rendered_test_groups)

            if not err:

                for group in tests_groups_to_run:

                    err = self._run_group( group,
                                         setup_only,
                                         cleanup_only,
                                         test_only,
                                         context )

        return err

    def _get_tests(self, test_names, rendered_tests):
        # return the list of tests to run
        # arg:
        #    test_names: string list of test names
        #    rendered_tests:  tests with rendered intrinsics
        # returns:
        #    tests_to_run: list of tests objects to be run
        #    err: string holding error message if or more names in test_names
        #         fails to match any existing test

        tests_to_run = []
        err = ""

        for test_name in test_names:

            this_test = search("[?name=='%s']"%test_name,rendered_tests,[])

            if this_test:
                tests_to_run = tests_to_run + this_test
            else:
                err = "test %s not found"%test_name

        return tests_to_run,err

    def _get_test_groups(self, group_names, test_groups):
        # return the list of test groups to run
        # arg:
        #    group_names: array of group names, where each group name
        #                 can optionally include a test name within the
        #                 group (e.g. ['group-b',group-a:test-b',etc])
        #    test_groups: all test groups
        #
        # returns:
        #    groups_to_run: list of test group objects to be run
        #    err: string holding error message if one or more names in group_names
        #         fails to match any existing test group

        groups_to_run = []
        err = ""

        for group_name in group_names:

            # see if group name includes a test name
            if ":" in group_name:
                name_parts = group_name.split(":")
                group_name_key = name_parts[0]
                test_name = name_parts[1]
            else:
                group_name_key = group_name
                test_name = ""

            this_group = search("[?name=='%s'] | [0]"%group_name_key,test_groups,{})

            if this_group:

                if test_name:
                    # isolate the test from the group
                    this_test = search("tests[?name=='%s'] | [0]"%test_name,this_group,{})

                    if this_test:
                        # only include this test
                        this_group['tests'] = [this_test]
                    else:
                        err = "test '%s' not found in test group '%s'"%(test_name,group_name_key)

                groups_to_run = groups_to_run + [this_group]

            else:
                err = "test group '%s' not found"%group_name

        return groups_to_run,err

    # run individual test
    def _run_test(self,
                  test,
                  setup_only=False,
                  cleanup_only=False,
                  test_only=False,
                  context=""):

        print("running test: %s ..."%test['name'])

        # target can be a url or a lookup into target map.
        # note: the test schema requires a target for all tests
        target = self.get_target(test['target'])

        err = ""

        if 'setup' in test and not (cleanup_only or test_only):

            setup_module = test['setup']

            # run the setup function
            print("running setup function at %s ..."%setup_module)

            err = self._run_setup(test['name'], target, setup_module)

        # if this is an artillery-based test, use the Artiller driver class
        # to execute tests and assertions
        if (not err and
            'artillery' in test and not (setup_only or cleanup_only) ):

            # localize the config path
            self.localize_config_path(test['artillery'])

            # initialize an artillery test driver
            artillery = ArtilleryDriver(test['name'],
                                        target,
                                        test['artillery'],
                                        self.test_results,
                                        self.params)

            # execute test and save statistics to test_results
            # using the driver
            artillery.run()

        # if this is a custom test, call the test_driver() method to
        # execute tests and assertions
        if (not err and
            'driver' in test and not (setup_only or cleanup_only)):

            # initialize a custom test driver
            custom_driver = CustomDriver(test['name'],
                                        target,
                                        test['driver'],
                                        self.test_results,
                                        self.params,
                                        context)

            # execute test and save statistics to test_results
            # using the driver
            custom_driver.run()

        if (not err and
            'cleanup' in test and not (setup_only or test_only)):

            cleanup_module = test['cleanup']

            print("running cleanup function at %s..."%cleanup_module)

            err = self._run_cleanup(test['name'], target, cleanup_module)

        return err

    # run individual test group
    def _run_group( self,
                    group_descriptor,
                    setup_only=False,
                    cleanup_only=False,
                    test_only=False,
                    context=""):

        print("running test group %s ..."%group_descriptor['name'])

        # target can be a url or a lookup into target map.
        # note: the group schema requires a target for all groups
        target = self.get_target(group_descriptor['target'])

        err = ""

        if 'setup' in group_descriptor and not (cleanup_only or test_only):

            setup_module = group_descriptor['setup']

            # run the setup function
            print("running setup function %s ..."%setup_module)

            err = self._run_setup(group_descriptor['name'],
                                  target,
                                  setup_module)

        # run tests in the test group
        if (not err and
            not (setup_only or cleanup_only)):

            for test in group_descriptor['tests']:

                self._run_test(test,
                               setup_only,
                               cleanup_only,
                               test_only,
                               context)

        if (not err and
            'cleanup' in group_descriptor and not (setup_only or test_only)):

            cleanup_module = group_descriptor['cleanup']

            print("running cleanup function at %s..."%cleanup_module)

            err = self._run_cleanup(group_descriptor['name'],
                                    target,
                                    cleanup_module)

        return err

    # localize the config path
    def localize_config_path(self, artillery_descriptor):

        test_path = artillery_descriptor['config']

        servicefile_path = self.params.get('servicefile-path')

        artillery_descriptor['config'] = localize_file(test_path, servicefile_path)

    def _run_setup(self,
                   name,
                   target,
                   module_rel_path):

        err = ""

        servicefile_path = self.params.get("servicefile-path")

        module, err = get_module(module_rel_path, servicefile_path)

        if not err:

            if hasattr(module,'test_setup'):
                # call the test_setup fxn in the module
                err = module.test_setup(target, self.params)
            else:

                err = ("setup module %s does not have a " +
                       "'test_setup' function"%module_rel_path)

        return err

    def _run_cleanup(self,
                     name,
                     target,
                     module_rel_path):

        err = ""

        servicefile_path = self.params.get("servicefile-path")

        module, err = get_module(module_rel_path, servicefile_path)

        if not err:

            if hasattr(module,'test_cleanup'):
                # call the test_cleanup fxn in the module
                err = module.test_cleanup(target, self.params)
            else:

                err = ("setup module %s does not have a " +
                       "'test_cleanup' function"%module_rel_path)

        if err:
            self.test_results.failing_test(name,err)

        return err

    def save_test_results(self):

        if self.results_store:

            destination_path = self.results_store['path']

            print("saving results to results store ... ")

            for result_file in self.test_results.get_results_files():

                file_name = os.path.basename(result_file)

                if 's3:' in destination_path:

                    # this will throw an exception if tester does not have a
                    # fresh credentials file in place. we let the exception
                    # escape here s.t. the resulting failure message will
                    # be easier to read/troubleshoot.
                    destination_s3_url = os.path.join(destination_path,file_name)
                    print("saving %s to %s... "%(result_file,destination_s3_url))
                    self.cp_file_to_s3(result_file, destination_s3_url)

    def cp_file_to_s3(self, source_file, destination_s3_url):
       # cp a file to an s3 bucket

        # make sure source file exists
        if os.path.exists(source_file):

            # form aws cp command for this file
            # aws_cmd = "aws s3 cp %s %s"%( source_file, destination_s3_url)

            # push the vault dictionary to s3
            session = boto3.Session(profile_name=self.profile)
            s3 = session.resource('s3')

            # separate s3 bucket and path from url
            destination_parts = destination_s3_url.split("/")
            s3_bucket = destination_parts[1]
            s3_path = "/".destination_parts[2:]

            # uploading contents to s3
            s3.meta.client.upload_file(source_file,
                                       s3_bucket,
                                       s3_path)

        else:
            raise FileError("Source file %s does not exist"%source_file)

    def get_target(self, target):

        target_out = target

        if ( self.target_map and target in self.target_map ):
            # the target specified is a lookup into
            # the target map
            target_out = self.target_map[target]

        return target_out

class TestResults():

    def __init__( self ):

        self.passing_tests = []
        self.failing_tests = []
        self.results_files = []
        # capture start time
        self.start_time=datetime.datetime.now()

    def get_failing_tests(self):
        return self.failing_tests

    def get_passing_tests(self):
        return self.passing_tests

    def get_num_tests(self):
        return len(self.passing_tests) + len(self.failing_tests)

    def get_results_files(self):
        return self.results_files

    def passing_test(self, test_name):
        self.passing_tests = self.passing_tests + [test_name]

    def failing_test(self, test_name, fail_msg):
        self.failing_tests = self.failing_tests + [{ "test": test_name,
                                                     "msg": fail_msg}]

    def assert_true(self, test_name, assertion_bool, assertion_desc="assertion failed"):
        if assertion_bool:
            self.passing_test(test_name)
        else:
            self.failing_test(test_name, assertion_desc)

    def assert_false(self, test_name, assertion_bool, assertion_desc="assertion failed"):
        if not assertion_bool:
            self.passing_test(self, test_name)
        else:
            self.failing_test(self, test_name, assertion_desc)

    def append_results_file( self, file_path ):
        self.results_files = self.results_files + [file_path]

    def get_test_duration_sec(self):
        return (datetime.datetime.now()-self.start_time).seconds

    # process results and generate an actionable exit code
    def process(self):

        # default with a successful exit code
        exit_code = 0

        test_duration_sec = self.get_test_duration_sec()

        num_tests = self.get_num_tests()

        if len(self.failing_tests)==0:

            print(self.get_stdout_divider("-"))
            print("Ran %s test in %s sec\n"%(num_tests, test_duration_sec))
            print("OK")

        else:

            print(self.get_stdout_divider("="))

            for failed_test in self.failing_tests:

                print("FAIL: %s"%failed_test['test'])
                print(self.get_stdout_divider("-"))
                print("%s\n"%failed_test['msg'])

            print(self.get_stdout_divider("-"))
            print("Ran %s test in %s sec\n"%(num_tests, test_duration_sec))
            print("FAILED (failures=%s)"%len(self.failing_tests))

            # set an unsuccessful exit code
            exit_code = 1

        return exit_code

    def get_stdout_divider(self,character):

        divider=""
        for i in range(0,70):
            divider = divider + character
        return divider
