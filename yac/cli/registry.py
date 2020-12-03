import argparse, json, os
from yac.lib.registry import set_private_registry, get_private_registry, clear_private_registry


def main():

    parser = argparse.ArgumentParser('Manage my yac registry')

    # optional args
    parser.add_argument('--set',      help='set the url and port of your private registry as <host>:<port>')
    parser.add_argument('--show',     help='show the registry currently configured',
                                      action='store_true')
    parser.add_argument('--clear',    help='clear the private registry currently configured',
                                      action='store_true')

    args = parser.parse_args()

    if args.set:

        host_parts = args.set.split(":")

        if len(host_parts) == 2 and host_parts[0] and host_parts[1]:
            redis_host = host_parts[0]
            redis_port = host_parts[1]

            private_registry = {"host": redis_host, "port": redis_port}

            set_private_registry(private_registry)

        else:
            print("Could not find host parts. An example private registry is: my-registyr.my-company.com:6379. Please try again")

    if args.show:

        private_registry = get_private_registry()

        if private_registry:
            print(json.dumps(private_registry, indent=4))
        else:
            print("No private registry is currently configured. The public registry will therefore be used.")

    if args.clear:

        print("Clearing private registry preferences currently in place")
        input("Hit Enter to continue >> ")

        clear_private_registry()
