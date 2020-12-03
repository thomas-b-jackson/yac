import json
from yac.lib.file import get_file_contents
from yac.lib.template import apply_stemplate

def do_calc(calc_arg, params):
    # Return a list of boot script lines, one per script line provided in params.
    # List is intended to be incorporated into the UserData portion of an EC2 or LaunchConfiguration
    # template.
    # args:
    #   calc_arg: array containing single element: a string holding path to boot script file

    boot_script_list=[]
    err = ""

    servicefile_path = params.get("servicefile-path")

    boot_file = calc_arg[0] if len(calc_arg)==1 else ""

    if boot_file:

        boot_script_contents = get_file_contents(boot_file,servicefile_path)

        if boot_script_contents:

            # render template variables into the file contents
            boot_script_contents = apply_stemplate(boot_script_contents, params)

            # split script into lines
            boot_script_lines_list = boot_script_contents.split('\n')

            for i,line in enumerate(boot_script_lines_list):

                if ("{" in line and "}" in line and "Ref" in line):
                    # this line contains a cloud formation reference which needs to be broken out
                    # i.e. something like ...
                    # CLUSTER_NAME={"Ref": "ECS"}

                    prefix = line[:line.index('{')]
                    reference = line[line.index('{'):line.index('}')+1]

                    reference_dict = json.loads(reference)

                    boot_script_list = boot_script_list + [prefix,{"Ref": reference_dict["Ref"]}] + ["\n"]

                else:
                    boot_script_list = boot_script_list + [line] + ["\n"]
        else:
            err = "boot file %s does not exist or has no content"%boot_file

    else:
        err = "No boot script provided"

    return boot_script_list,err

# for debugging
def pp_script(boot_script_list):

    for line in boot_script_list:
        print(str(line))

