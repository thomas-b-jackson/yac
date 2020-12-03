import os, argparse
from yac.lib.service import get_service

def main():

    parser = argparse.ArgumentParser('Print a yac service to a cloud provider')

    # required args
    parser.add_argument('servicefile',   help='location of the Servicefile (registry key or abspath)')

    # optional
    # store_true allows user to not pass a value (default to true, false, etc.)
    parser.add_argument('-p',
                        '--params', help='path to a file containing static service parameters (useful for keeping stack in config mgmt)')
    parser.add_argument('-a',
                        '--alias',  help='override default service alias with this value (used for stack resource naming')

    parser.add_argument('-d',
                        '--dryrun', help='dry run the stack change, printing template to stdout',
                                    action='store_true')
    parser.add_argument('-k',
                        '--kvps',   help='params as comma-separated, key:value pairs')

    parser.add_argument('--delete', help='delete the stack',
                                    action='store_true')
    parser.add_argument('-c',
                        '--context',help='the build context')

    args = parser.parse_args()

    service,err = get_service(args.servicefile,
                               args.alias,
                               args.params,
                               args.kvps)

    if not err:

        # get the stack associated with the service
        stack = service.get_stack()

        if stack and not args.delete:
            # perform the build
            err = stack.build(service.get_all_params(),
                              deploy_mode_bool = False,
                              dry_run_bool = args.dryrun,
                              context = args.context)

            # exit with an appropriate exit code
            if err:
                print("stack build failed with error: %s"%err)
                exit(1)
            else:
                print("stack build completed")
                exit(0)

        elif stack and args.delete:

            err = stack.delete(service.get_all_params())

            # exit with an appropriate exit code
            if err:
                print("stack deletion failed with error: %s"%err)
                exit(1)
            else:
                print("stack deletion completed")
                exit(0)
        else:
            print("service %s does not have a buildable stack"%args.servicefile)

    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)

