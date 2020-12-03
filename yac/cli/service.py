#!/usr/bin/env python

import argparse, sys, json, os
from yac.lib.service import register_service, clear_service
from yac.lib.service import get_service_by_name, get_service
from yac.lib.service import get_all_service_names

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg

def main():

    parser = argparse.ArgumentParser('Share a service with others via the yac registry')

    parser.add_argument('--share',
                        help=('register a service with the yac service registry so it can be provisioned by others.' +
                        ' (arg is the path to the Servicefile)'),
                        type=lambda x: is_valid_file(parser, x))
    parser.add_argument('--ver',  help='the version label to associate with this service')
    parser.add_argument('--show',  help='show a service (arg is the service key)')
    parser.add_argument('--clear', help='clear a service from the registry  (arg is the service key)')
    parser.add_argument('--find',  help=('find a service in the registry via a search string '+
                                         '(arg is search string into the registry)'))

    # pull out args
    args = parser.parse_args()

    if args.share:

        service, err = get_service(args.share)

        if not err:

            service_version = get_service_version(service, args.ver)

            if not service_version:

                print("Please specify a version label via the --ver argument")
                exit()

            service_name = "%s:%s"%(service.description.name,service_version)

            # see if service has already been registered
            service_in_registry = get_service_by_name(service_name)

            if not service_in_registry:
                challenge = input("Please input a challenge phrase to control updates to your service definition >> ")
            else:
                challenge = input("Please input the challenge phrase associated with this service definition >> ")


            print(("About to register service '%s' with challenge phrase '%s'. ")%(service_name,challenge))
            input("Hit Enter to continue >> ")

            err = register_service(service_name, args.share, challenge)

            if not err:

                print(("Your service has been registered with yac under the key: '%s' and challenge phrase '%s'.\n" +
                       "You will prompted for the challenge phrase if you attempt to update your service.\n" +
                       "Other users can run your service via '>> yac stack %s ...'")%(service_name,challenge,service_name))
            else:
                print(("Your service registration failed with error: %s"%err))


        elif args.clear:

            print("Clearing the '%s' service from registry"%(args.clear))
            challenge = input("Please input the challenge phrase associated with this service >> ")
            input("Hit Enter to continue >> ")

            clear_service(args.clear, challenge)

        elif args.find:
            all_params = get_all_service_names(args.find)
            print(all_params)

        elif args.show:

            service = get_service(args.show)

            print(service)

        else:
            print("servicefile could not be loaded from %s"%args.servicefile)
            print("error: %s"%err)

def get_service_version(service, vers_arg):

    service_version = ""

    if vers_arg:
        service_version = vers_arg

    elif service.description.version:
        service_version = service.description.version

    return service_version