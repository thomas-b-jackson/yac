#!/usr/bin/env python

import argparse
from yac.lib.service import get_service

def load_into_list(name_str):

    return name_str.split(",") if name_str else []

def main():

    parser = argparse.ArgumentParser(description='Run a task per the task defintions in the provided Servicefile')

    # required args
    parser.add_argument('servicefile', help='location of the Servicefile (registry key or abspath)')


    parser.add_argument('-t',
                        '--tests',    help="comma-separated list of tests to run (defaults to all tests)")
    parser.add_argument('-g',
                        '--groups',   help="comma-separated list of test groups (or group-name:test-name tuples) to run (defaults to all test groups)")


    parser.add_argument('-p',
                        '--params', help='path to a file containing static service parameters (useful for keeping stack in config mgmt)')
    parser.add_argument('-a',
                        '--alias',   help='service alias for the stack currently supporting this service (deault alias is per Servicefile)')
    parser.add_argument('-k',
                        '--kvps',    help='params as comma-separated, key:value pairs')

    parser.add_argument('-s',
                        '--setup',   help='run test setup only (used with --name or --group arg)',
                                       action='store_true')
    parser.add_argument('-c',
                        '--cleanup', help='run test cleanup only (used with --name or --group arg)',
                                       action='store_true')
    parser.add_argument('-o',
                        '--only',    help='run test or group only with no setup or cleanup (used with --name or --group arg)',
                                       action='store_true')

    args = parser.parse_args()

    service,err = get_service(args.servicefile,
                               args.alias,
                               args.params,
                               args.kvps)

    if not err:

        # get all integration tests
        integration_tests = service.get_tests()

        # use default context
        context = ""

        if args.tests and not args.groups:
            tests_to_run = load_into_list(args.tests)
            groups_to_run = []

        elif args.groups and not args.tests:
            tests_to_run = []
            groups_to_run = load_into_list(args.groups)

        elif args.groups and args.tests:
            tests_to_run = load_into_list(args.tests)
            groups_to_run = load_into_list(args.groups)

        elif not args.tests and not args.groups:
            tests_to_run = integration_tests.get_test_names()
            groups_to_run = integration_tests.get_group_names()

        # run tests
        err = integration_tests.run(service.get_all_params(),
                                    context,
                                    tests_to_run,
                                    groups_to_run,
                                    args.setup,
                                    args.cleanup,
                                    args.only)

        if not err:

            # save test results to results store
            integration_tests.save_test_results()

            test_results = integration_tests.get_results()

            # process test results and generate an actionable exit code
            exit_code = test_results.process()

            # exit with an exit code based on results
            exit(exit_code)

        else:

            print("integration testing failed with error: %s"%err)
            exit(1)

    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)