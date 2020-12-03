import argparse,sys,os

import yac.cli.stack
import yac.cli.service
import yac.cli.secrets
import yac.cli.registry
import yac.cli.task
import yac.cli.deploy
import yac.cli.make
import yac.cli.test
import yac.cli.credentials
import yac.cli.params
import yac.cli.grok
from yac.cli.primer import show_primer

def main():

    cli_alias_map = get_cli_alias_map()
    command_options = get_command_options(cli_alias_map)

    # first argument is help
    if (len(sys.argv)==1 or sys.argv[1] == '-h'):

        show_primer('primer','primer',command_options)

    elif sys.argv[1] not in list(cli_alias_map.keys()):
        return "the command '%s' is not yet implemented"%sys.argv[1]

    # last argument is primer
    elif sys.argv[len(sys.argv)-1] == 'primer':

        # show primer instructions
        command = cli_alias_map[sys.argv[1]]
        show_primer(command,sys.argv[1],command_options)

    else:

        # strip command from args list
        command = sys.argv[1]
        sys.argv = sys.argv[1:]

        if cli_alias_map[command] == 'make':

            return yac.cli.make.main()

        elif cli_alias_map[command] == 'deploy':

            return yac.cli.deploy.main()

        elif cli_alias_map[command] == 'stack':

            return yac.cli.stack.main()

        elif cli_alias_map[command] == 'test':

            return yac.cli.test.main()

        elif cli_alias_map[command] == 'service':

            return yac.cli.service.main()

        elif cli_alias_map[command] == 'secrets':

            return yac.cli.secrets.main()

        elif cli_alias_map[command] == 'registry':

            return yac.cli.registry.main()

        elif cli_alias_map[command] == 'task':

            return yac.cli.task.main()

        elif cli_alias_map[command] == 'creds':

            return yac.cli.credentials.main()

        elif cli_alias_map[command] == 'params':

            return yac.cli.params.main()

        elif cli_alias_map[command] == 'grok':

            return yac.cli.grok.main()

def get_cli_alias_map():

    cli_alias_map = {
        'deploy': 'deploy',
        'make':   'make',
        'artifact': 'make',
        'art':    'make',
        'fact':   'make',
        'stack':  'stack',
        'build':  'stack',
        'test':   'test',
        'service': 'service',
        'secrets': 'secrets',
        'secret':  'secrets',
        'registry':'registry',
        'task':    'task',
        'creds':   'creds',
        'cred':    'creds',
        'credentials': 'creds',
        'param':   'params',
        'params':  'params',
        'parameters': 'params',
        'grok':    'grok',
        'ex':      'grok',
        'examples': 'grok'
    }

    return cli_alias_map

def get_command_options(get_cli_alias_map):

    command_options_map = {}
    for key in list(get_cli_alias_map.keys()):
        if get_cli_alias_map[key] in list(command_options_map.keys()):
            command_options_map[get_cli_alias_map[key]].append(key)
        else:
            command_options_map[get_cli_alias_map[key]] = [key]
    return command_options_map
