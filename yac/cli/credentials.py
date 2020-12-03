#!/usr/bin/env python

import argparse
from yac.lib.service import get_service

def main():

    parser = argparse.ArgumentParser(description='Create credentials per Servicefile')

    # required args
    parser.add_argument('servicefile', help='location of the Servicefile (registry key or local path)')
    parser.add_argument('credsname',        help='name of the credentialer to run')
    parser.add_argument('-k',
                        '--kvps',   help='params as comma-separated, key:value pairs')
    parser.add_argument('-o','--overwrite', help='overwrite any existing credentials file',
                                            action='store_true')

    args = parser.parse_args()

    service,err = get_service(args.servicefile,
                             "",
                             "",
                             args.kvps)

    if not err:

        credentializer = service.get_credentialers()

        if credentializer:

            err = credentializer.create(args.credsname,
                                        service.get_params(),
                                        service.get_vaults(),
                                        args.overwrite)

            if err:
                print("credential creation failed with error:\n")
                print(err)

        else:

            print("servicefile input lacks credentialer instructions. aborting credential creation")
    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)