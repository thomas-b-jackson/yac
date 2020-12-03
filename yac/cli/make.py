#!/usr/bin/env python

import argparse
from yac.lib.service import get_service

def main():

    parser = argparse.ArgumentParser(description='Build an artifact per the Artifacts specified in the Servicefile')

    # required args
    parser.add_argument('servicefile', help='location of the Servicefile (registry key or abspath)')
    parser.add_argument('-n',
                        '--name',      help="name of the artifact to make")
    parser.add_argument('-p',
                        '--params',    help='path to a file containing additional, static, service parameters (e.g. vpc params, of service constants)')
    parser.add_argument('-k',
                        '--kvps',   help='params as comma-separated, key:value pairs')
    parser.add_argument('-d',
                        '--dryrun',  help='dry run',
                                    action='store_true')

    args = parser.parse_args()


    service, err = get_service(args.servicefile,
                         "",
                         args.params,
                         args.kvps)

    if not err:

        # get the artifacts associated with this service
        artifacts = service.get_artifacts()

        if args.name and args.name not in artifacts.get_names():
            print("artifact '%s' does not exist. available artifacts include:\n\n%s"%(args.name,
                                                                                artifacts.pprint()))

        else:
            # make the artifacts
            err = artifacts.make(service.get_params(),
                                 service.get_vaults(),
                                 args.name,
                                 args.dryrun)

            if err:
                # the artifact is not available. show available artifacts
                print("build error: %s"%err)
                exit(1)
    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)
