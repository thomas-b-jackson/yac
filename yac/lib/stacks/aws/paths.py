import os

def get_credentials_path():

    return os.path.join(os.path.expanduser("~"),
                                           ".aws",
                                           "credentials")

def get_configs_path():

    return os.path.join(os.path.expanduser("~"),
                                           ".aws",
                                           "config")