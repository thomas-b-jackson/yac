#!/usr/bin/env python

import argparse
from yac.lib.engines import register_engine

def main():

    parser = argparse.ArgumentParser(description='Register a new engine (stack, vaults, credentialer, etc.)')

    # required args
    parser.add_argument('type',    help='engine type',
                                   choices=['stack', 'credentialer', 'maker', 'vault'])
    parser.add_argument('key',     help='engine key')
    parser.add_argument('module',    help="path to the python file implementing the engine")
    parser.add_argument('class_name', help='name of class implementing the engine')
    args = parser.parse_args()

    err = register_engine(args.type,
                          args.key,
                          args.module,
                          args.class_name)

    # exit with an appropriate exit code
    if err:
        print("engine registration failed with error: %s"%err)
        exit(1)
    else:
        print("engine was successfully registered")
        exit(0)