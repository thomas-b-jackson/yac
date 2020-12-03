#!/usr/bin/env python

import logging, logging.config, json, os
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.params import Params
from yac.lib.paths import get_root_path


def get_deploy_logger(logs_full_path, log_level="INFO"):

    logger_configs = _get_logger_configs(logs_full_path, log_level)

    # load the dictionary-style configs
    logging.config.dictConfig( logger_configs )

    # return a logger that logs to both the file and to stdout 
    logger = logging.getLogger('yac_deploy')

    return logger

def get_stack_logger(logs_full_path, log_level="INFO"):

    logger_configs = _get_logger_configs(logs_full_path, log_level)

    # load the dictionary-style configs
    logging.config.dictConfig( logger_configs )

    # return a logger that logs to both the file and to stdout 
    logger = logging.getLogger('yac_stack')

    return logger

def get_test_logger(logs_full_path, log_level="INFO"):

    logger_configs = _get_logger_configs(logs_full_path, log_level)

    # load the dictionary-style configs
    logging.config.dictConfig( logger_configs )

    # return a logger that logs to both the file and to stdout 
    logger = logging.getLogger('yac_test')

    return logger

def get_yac_logger(log_level="INFO"):

    logger_configs = _get_logger_configs("/tmp/yac.logs", log_level)

    # load the dictionary-style configs
    logging.config.dictConfig( logger_configs )

    # return a logger that logs to both the file and to stdout 
    logger = logging.getLogger('yac')

    return logger

def _get_logger_configs( logs_full_path, log_level="INFO"):

    logs_path = os.path.dirname(logs_full_path)

    if not os.path.exists(logs_path):
        os.makedirs(logs_path)

    logger_configs_with_refs = {}

    with open(os.path.join(get_root_path(),
                           "config/logger.conf"), 'r') as config_file:
        logger_configs_with_refs = json.load(config_file)

    key_values = Params({})
    key_values.set("log-level", log_level)

    key_values.set("deploy-log-path", logs_full_path)

    # render log level and log path into logger configs
    return apply_intrinsics(logger_configs_with_refs, key_values)
