import argparse,sys,os
from yac.lib.paths import get_root_path

def show_primer(command,alias,command_options):

    path_elements = [get_root_path(),'primer']

    if command != 'primer':
        path_elements.append(command)
    path_elements.append('primer')

    # make sure primer exists
    primer_file = os.path.join( *path_elements)
    if not os.path.exists(primer_file):

        print("Primer not available for the command input")

    else:
        with open(os.path.join( *path_elements)) as primer_file:
            primer_file_content = primer_file.read()

        # render yac version
        rendered_content = primer_file_content.replace("{VER}",get_version())
        # render command
        rendered_content = rendered_content.replace("{COMMAND}",alias)
        # render command options
        rendered_content = rendered_content.replace("{COMMANDS}",pp_command_options(command_options))
        # show primer text
        print(rendered_content)

def get_version():

	version=""

	with open(os.path.join(get_root_path(),'cli/.ver'), 'r') as myfile:
	  version = myfile.read()

	return version

def pp_command_options(command_options_map):
    options = ""
    for key in command_options_map:
        options = options + "* %s"%" || ".join(command_options_map[key]) + "\n"
    return options