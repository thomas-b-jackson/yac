#!/usr/bin/env python

import argparse
from yac.lib.service import get_service

def main():

    parser = argparse.ArgumentParser(description='Run a task per the task defintions in the provided Servicefile')

    # required args
    parser.add_argument('servicefile', help='location of the Servicefile (registry key or abspath)')
    parser.add_argument('name',        help="name of task to run (or 'help' to see all availble task)")
    parser.add_argument('-p',
                        '--params',    help='path to a file containing additional, static, service parameters (e.g. vpc params, of service constants)')
    parser.add_argument('-a',
                        '--alias',     help='service alias for the stack currently supporting this service (deault alias is per Servicefile)')
    parser.add_argument('-k',
                        '--kvps',      help='params as comma-separated, key:value pairs')
    args = parser.parse_args()


    service,err = get_service(args.servicefile,
                         args.alias,
                         args.params,
                         args.kvps)

    if not err:

        # get the tasks associated with this service
        tasks = service.get_tasks()

        # verify task is available
        if tasks.get(args.name):

            # run this task
            err = tasks.run(args.name,
                            service.get_all_params())

            if err:

                print("The task failed with error: %s"%err)

        else:

            # the task is not available. show available tasks

            print("The task '%s' was not recognized"%args.name)

            print("Available tasks include:")
            for task_name in tasks.get_names():
                task = tasks.get(task_name)
                print("%s: %s"%(task_name,task.description))

    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)