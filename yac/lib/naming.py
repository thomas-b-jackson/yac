#!/usr/bin/env python
import time, os, json
from yac.lib.schema import validate

def get_stack_name(params):

    return get_resource_name(params,"stack")

def get_resource_name(params, resource_str):

    """ Called via the yac-name intrinsic to generate a name for a
        given service resource

    Args:
        params: A Params instance
        resource_str: string containing an arbitrary resource name

    Returns:
        A string containing the resource name

    Raises:
        ValidationError: if a custom naming convention fails schema validation

    """

    default_naming_convention = {
        "param-keys": ['prefix','service-alias'],
        "delimiter": "-"
    }

    # allow a given service to override the default convention
    # via a "naming-convention" param
    naming_convention = params.get("naming-convention",
                                    default_naming_convention)

    # print naming_convention

    # validate. this will raise a validation error if
    # required fields aren't present
    validate(naming_convention, "yac/schema/naming.json")

    delimiter = ""
    if 'delimiter' in naming_convention:
        delimiter = naming_convention['delimiter']

    if not delimiter and 'delimitter' in naming_convention:
        # older versions of yac allowed a mispelled version of
        # the delimiter attribute
        delimiter = naming_convention['delimitter']
        print("warning: the naming-convention 'delimitter' attribute has been deprecated")
        print("use the 'delimiter' attribute instead ...")

    name_elements = []
    for param_key in naming_convention['param-keys']:
        name_elements.append(params.get(param_key,''))

    # add the resource
    if resource_str != "stack":
        name_elements.append(resource_str)

    # get rid of empty strings
    name_parts = [_f for _f in name_elements if _f]

    # separate the part with the delimiter
    resource_name = delimiter.join(name_parts)

    return resource_name