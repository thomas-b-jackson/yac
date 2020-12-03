#!/usr/bin/env python

import argparse
from yac.lib.pipeline import Pipeline
from yac.lib.service import get_service

def main():

    parser = argparse.ArgumentParser(description='Run a task per the task defintions in the provided Servicefile')

    # required args
    parser.add_argument('servicefile', help='location of the Servicefile (registry key or local path)')

    parser.add_argument('-a',
                        '--alias',   help='service alias for the stack currently supporting this service (deault alias is per Servicefile)')

    parser.add_argument('-g',
                        '--stages',  help='stages to deploy, as comma-separated names')

    parser.add_argument('-d',
                        '--dryrun',  help='dry run',
                                     action='store_true' )
    parser.add_argument('-k',
                        '--kvps',   help='params as comma-separated, key:value pairs')

    parser.add_argument('-p',
                        '--params', help='path to a file containing static service parameters (useful for keeping stack in config mgmt)')


    args = parser.parse_args()

    service, err = get_service(args.servicefile,
                          args.alias,
                          args.params,
                          args.kvps)

    if not err:

      pipeline = service.get_pipeline()

      if pipeline:

        if args.stages:
          stages_array = args.stages.split(',')
        else:
          stages_array = []

        # deploy the service
        pipeline.deploy(service,
                        stages_array,
                        args.dryrun)
      else:
        print("servicefile input lacks pipeline instructions. aborting deploy")

    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)