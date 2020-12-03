#!/usr/bin/env python

import argparse
from yac.lib.service import get_service

def main():

    parser = argparse.ArgumentParser(description='View the params available for a given servicefile')

    # required args
    parser.add_argument('servicefile', help='location of the Servicefile (registry key or abspath)')
    parser.add_argument('-p',
                        '--params',    help='path to a file containing additional, static, service parameters (e.g. vpc params, of service constants)')
    parser.add_argument('-a',
                        '--alias',     help='service alias for the stack currently supporting this service (deault alias is per Servicefile)')
    parser.add_argument('-k',
                        '--kvps',      help='params as comma-separated, key:value pairs')
    parser.add_argument('-b',
                        '--build_context', help='an optional build context (per pipeline stages)')
    parser.add_argument('-c',
                        '--creds_keys', help='comma-separated list of credentialer keys (e.g aws,k8s)')
    parser.add_argument('-d',
                        '--dryrun',    help='see what if any params change in a dry run condition',
                                       action='store_true')
    parser.add_argument('-v',
                        '--view', help='view value of an individual param, indentified by its key')


    args = parser.parse_args()


    service,err = get_service(args.servicefile,
                         args.alias,
                         args.params,
                         args.kvps)

    if service:

        # get the constants, inputs, secrets and metadata associated with this service
        # (i.e. "all of the params")
        creds_key_array = args.creds_keys.split(',') if args.creds_keys else []

        params = service.get_all_params(args.build_context,
                                        args.dryrun,
                                        creds_key_array)

        if args.view:
            # view the value of a specific param
            param = params.get(args.view)

            if param:
                print("%s: %s"%(args.view,param))
            else:
                print("param '%s' not found"%args.view)

        else:
            # show all of the params
            print(params)

    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)