import os

def get_config_path():

    config_path = os.path.join(os.path.dirname(__file__),'../','config')

    return config_path

def get_root_path():

    root_path = os.path.join(os.path.dirname(__file__),'../')

    return root_path

def get_yac_path():

    yac_path = os.path.join(os.path.dirname(__file__),'../../')

    return yac_path

def get_lib_path():

    lib_path = os.path.join(os.path.dirname(__file__))

    return lib_path

def get_dump_path(service_alias=""):
    # Ruturns a path that can serve as a handy 'dumping' ground for rendered files
    # args:
    #   service_alias: the alias of the service
    # returns:
    #   string containing the path where files can be dumped

    if service_alias:
        dump_path = os.path.join("/tmp",service_alias)
    else:
        dump_path = "/tmp"

    # create the directory if it does not alread exist
    if not os.path.exists(dump_path):
        os.makedirs(dump_path)

    return dump_path

def get_home_dump_path(service_name):
    # Return a std path under the user's home directory
    # Location can serve as a handy 'dumping' ground for rendered files
    #  during dry runs
    # args:
    #   service_name: the name of the service
    # returns:
    #   string containing an absolution path under the user's home directory

    home = os.path.expanduser("~")

    # if servicename includes a version, replace the colon separator
    # with a slash
    service_name_cleaned = service_name.replace(":", os.sep)

    dump_path = os.path.join(home,'.yac','tmp', service_name_cleaned)

    # create the directory if it does not alread exist
    if not os.path.exists(dump_path):
        os.makedirs(dump_path)

    return dump_path
