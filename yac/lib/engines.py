#!/usr/bin/env python
import os, json
from yac.lib.paths import get_root_path
from yac.lib.module import get_module
from yac.lib.search import search
from yac.lib.schema import validate

def get_stack_provider(stack_type, serialized_stack):

    return get_engine("stack",stack_type,serialized_stack)

def get_credentials_provider(credentialer_type, serialized_stack):

    return get_engine("credentialer",credentialer_type,serialized_stack)

def get_vault_provider(vault_type, serialized_vault):

    return get_engine("vault",vault_type,serialized_vault)

def load_artifact_obj(artifact_type, serialized_artifact):

    return get_engine("artifact",artifact_type,serialized_artifact)

def get_engine(engine_type, engine_key, serialized_obj):

    engine_configs = get_engine_configs()

    instance = None
    err = ""

    if engine_type:
        module_path = search("%s[?key=='%s'] | [0].module"%(engine_type,engine_key), engine_configs)
        class_name = search("%s[?key=='%s'] | [0].class"%(engine_type,engine_key), engine_configs)

        provider_module,err = get_module(module_path)

        if not err and class_name:
            class_ = getattr(provider_module, class_name)
            instance = class_(serialized_obj)

    return instance,err

def register_engine(engine_type,
                    engine_key,
                    module_path,
                    class_name,
                    configs_path=""):

    configs = get_engine_configs(configs_path)

    err = ""

    provider_module,err = get_module(module_path)

    if not err and class_name:
        class_ = getattr(provider_module, class_name)
        instance = class_({})


        # make sure engine does not already exist
        existing_module_path = search("%s[?key=='%s'] | [0].module"%(engine_type,engine_key), configs)

        if existing_module_path:
            err = "'%s' engine with key %s already exists"%(engine_type,engine_key)

        if not err:

            configs[engine_type].append({
                    "key": engine_key,
                    "module": module_path,
                    "class": class_name
                })

            # write the engine configs to disk
            write_engine_configs(configs, configs_path)

    return err

def write_engine_configs(engine_configs, dump_path=""):

    if not dump_path:
        # write them back to the default location
        dump_path = os.path.join(get_root_path(),"config/engines.json")

    engine_configs_str = json.dumps(engine_configs,indent=2)

    with open(dump_path, 'w') as the_file:
        the_file.write(engine_configs_str)

def get_engine_configs(configs_path=""):
    # raises:
    #   validation error if anything is missing

    if not configs_path:
        configs_path = os.path.join(get_root_path(),
                           "config/engines.json")

    engine_configs = {}
    with open(configs_path, 'r') as config_file:
        engine_configs = json.load(config_file)

    validate(engine_configs,"yac/schema/engines.json")
    return engine_configs