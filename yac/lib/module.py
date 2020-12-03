import os, imp
from yac.lib.file import get_localized_script_path

def get_module(module_path_arg, servicefile_path=""):

    err = ""
    module_name = 'yac.lib.customizations'
    script_module = None

    if module_path_arg:

        if os.path.exists(module_path_arg):
            module_path = module_path_arg
        else:
            # treat as a path relative to the servicefile
            module_path = get_localized_script_path(module_path_arg, servicefile_path)

        if module_path and os.path.exists(module_path):

            script_module = imp.load_source(module_name,module_path)

        else:
            # return a new, empty module
            script_module = imp.new_module(module_name)
            err = "module %s does not exist"%module_path

    else:
        err = "module %s does not exist"%module_path_arg

    return script_module, err
