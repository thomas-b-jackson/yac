#!/usr/bin/env python

import argparse, os, shutil
from yac.lib.examples import get_all_keys
from yac.lib.file import get_file_contents
from yac.lib.paths import get_home_dump_path
from yac.lib.service import get_service

def main():

    parser = argparse.ArgumentParser(description='View, test drive, or export service examples')

    # required args
    parser.add_argument('-v','--view',  help='key of service example to view (run "yac grok" with no args to show all examples)')
    parser.add_argument('-f',
                        '--file',    help='view individual file from an example, or from yac sources (i.e. schemas)')
    parser.add_argument('-x',
                        '--export',  help='export example service for customization',
                                     action='store_true')

    args = parser.parse_args()

    if not args.view and not args.file and not args.export:

        # show the keys of all available examples
        keys = get_all_keys()

        print("Available examples include:")
        for key in keys:
            print("examples/%s"%key)

    if args.view and not args.export:

        # show the contents of the servicefile
        file_contents = get_file_contents(args.view)

        if file_contents:
            print(file_contents)

    if args.file:

        if args.view:
            base_path = os.path.dirname(args.view)
        else:
            # assume the path is relative to yac
            base_path = ""

        # show the contents of the file
        file_contents = get_file_contents(os.path.join(base_path,args.file))

        if file_contents:
            print(file_contents)

    if args.export and args.view:

        # put the files in the std dump path so they
        #  can be viewed after the yac container stops

        src = os.path.dirname(os.path.join(args.view))

        # get servicealias
        service,err = get_service(args.view)

        print("made it here")

        dest = get_home_dump_path("%s/%s"%("examples",
                             service.get_description().get_alias()))

        # make sure destination is empty
        if os.path.exists(dest):
            shutil.rmtree(dest)

        # recreate destination
        # os.makedirs(dest)
        #
        # src_files = os.listdir(src)
        # for file_name in src_files:
        #     full_file_name = os.path.join(src, file_name)
        #     if (os.path.isfile(full_file_name)):
        #         shutil.copy(full_file_name, dest)
        shutil.copytree(src,dest)

        print("example exported to: %s"%dest)
