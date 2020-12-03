import json, boto3, jmespath, base64, os
from yac.lib.module import get_module
from yac.lib.file import localize_file
from yac.lib.stacks.aws.vpc import get_vpcs, get_subnet_ids
from yac.lib.paths import get_yac_path

def do_calc(calc_arg, params):

    """ Generates a parameter via a calculation, either via a
        'stock' calculator, or via a provided calculator module.

        stock calcs are describe in wiki on the 'yac calcs' page

    Args:
        calc_arg: argv-style list where:
                    * first item is either stock_calc_fxn_map or a path to a custom calc
                      module with a do_calc function
                    * remaining items are arguments to be pass to the function
        params:  a Params instance

    Returns:
        object: an object containing the calculated value
        err:  a string containing an error code

    Raises:
        None

    """

    stock_calc_fxn_map = {
        'vpc-id': calc_vpc_id,
        'subnet-ids': calc_subnet_ids,
        'ec2-boot': calc_ec2_user_data,
        'subnet-id': calc_subnet_id,
        'vpc-cidr': calc_vpc_cidr,
        'b64enc': calc_base64_encoding,
        'to_int':  calc_int,
        'configmaps-hash': calc_configmaps_hash,
        'secrets-hash': calc_secrets_hash
    }

    # initialize return values
    value = None
    err = ""

    calc_key = calc_arg[0]

    if calc_key in list(stock_calc_fxn_map.keys()):

        if len(calc_arg)>1:
            value,err = stock_calc_fxn_map[calc_key](params,calc_arg[1:])
        else:
            value,err = stock_calc_fxn_map[calc_key](params)

    else:

        localized_file_path = ""
        servicefile_path = params.get('servicefile-path',"")

        if os.path.exists(os.path.join(get_yac_path(),calc_key)):
            # calculator is part of yac (but renders intrinsics, so can't
            # be imported directly)
            localized_file_path = os.path.join(get_yac_path(),calc_key)
        else:
            # treat the argument as a custom calculator
            localized_file_path = localize_file(calc_key, servicefile_path)

        if localized_file_path:

            calc_module, err = get_module(localized_file_path, servicefile_path)

            if not err:
                argv = calc_arg[1:] if calc_arg[1:] else []
                try:
                    value,err = calc_module.do_calc(argv, params)

                except AttributeError as e:
                    err = "calling do_calc() against %s failed with error: %s"%(calc_key,e)
        else:
            err = "calc file %s does not exist"%calc_key

    return value, err

def calc_vpc_id(params):

    # see if vpc id has already be calculated
    cache_key="vpc-id"
    value = check_calc_cache(params,cache_key)
    err = ""
    if not value:
        vpc, err = get_vpc(params)
        if not err:
            value = vpc.id
            # update cache
            cache_calc(params, cache_key, value)

    return value, err

def calc_configmaps_hash(params):
    err = ""

    value = params.get("configmaps-hash","")

    if not value:
        err = "configmaps hash is not set"

    return value, err

def calc_secrets_hash(params):
    err = ""

    value = params.get("secrets-hash","")

    if not value:
        err = "secrets hash is not set"

    return value, err

def calc_vpc_cidr(params):

    # see if vpc cidr has already be calculated
    cache_key="vpc-cidr"
    value = check_calc_cache(params,cache_key)
    err = ""
    if not value:
        vpc, err = get_vpc(params)
        if not err:
            value = vpc.cidr_block
            # update cache
            cache_calc(params,cache_key, value)

    return value, err

def calc_ec2_user_data(params, arg_array):
    # converts a boot script into an array of strings, suitable for inclusion
    # in the UserData portion of a cloud formation template
    # args:
    #   arg_array: len 1 array containing a string representing the "boot_script_path"
    #
    #
    # returns:
    #   lines:  an array containing the lines of the UserData
    #   err:  a string containing an error message if a subnet matching the search string and az
    #           could not be found

    lines = []
    err = ""

    # the arg array for the calculator should contain the
    # path of the boot script
    if (len(arg_array) == 1 and
        type(arg_array[0]) is str):

        boot_file = arg_array[0]

    elif (len(arg_array) == 1 and
        type(arg_array[0]) is not str):

        err = ("The first argument should be a string containing the " +
              "path to the boot file")

    elif len(arg_array) == 0:

        err = ("An argument must be included: a string containing the " +
              "path to the boot file")

    if not err:
        # the boot module renders templates, which in turn leverage intrinsics.
        # importing the module directly would result in a link error
        # (since calcs are themselves an intrinsic) so run it this way
        lines,err = do_calc(["yac/lib/stacks/aws/boot.py",boot_file],params)

    return lines,err

def calc_subnet_ids(params, arg_array):
    # calculate the ids of a set of subnets
    # args:
    #   arg_array: array containing a string and array formatted as:
    #      ["<search string>",["<az1>","<az2>", etc]]
    #
    #   The search string is used to search among the subnets in the active vpc.
    #   The az array is used to select among the subnets returned.
    #
    # returns:
    #   ids:  an array containing the ids of the subnets as strings
    #   err:  a string containing an error message if a subnet matching the search string and az
    #           could not be found

    subnet_label = ""
    err = ""
    value = []

    # the arg array for the calculator should contain the
    # subnet label and the availability zones that the subnets
    # should correspond to
    if (len(arg_array) == 2 and
        type(arg_array[0]) is str and
        type(arg_array[1]) is list):

        subnet_label = arg_array[0]
        azs = arg_array[1]

    elif (len(arg_array) == 2 and
        type(arg_array[0]) is not str):

        err = ("The first argument should be a string that can be used " +
              "to calculate the desired subnets (e.g. 'internal' or 'dmz')")

    elif (len(arg_array) == 2 and
        type(arg_array[1]) is not list):

        err = ("The second argument must be an array of availability zones")

    elif len(arg_array) == 1:

        err = ("availability zones must be included as an array " +
               "to calculate subnet ids")

    if not err:

        # see if subnet ids have already been calculated
        cache_key = "subnet-id-%s-%s"%(subnet_label,str(azs))
        value = check_calc_cache(params,cache_key,[])

        if not value:

            vpc, err = get_vpc(params)

            if not err:

                # get the subnet id with label and az provided
                subnet_ids,err = get_subnet_ids(vpc,
                                                azs,
                                                params,
                                                subnet_label)

                if not err and subnet_ids:
                    value =  subnet_ids
                    cache_calc(params, cache_key, value)

    return value, err

def calc_subnet_id(params, arg_array):
    # calculate the id of a single subnet
    # args:
    #   arg_array: array containing two strings ["<search string>","<az>"]
    #
    #   The search string is used to search among the subnets in the active vpc.
    #   The az is used to select among the subnets returned.
    #
    # returns:
    #   id:  a string containing the id of the subnet
    #   err: a string containing an error message if a subnet matching the search string and az
    #        could not be found

    subnet_label = ""
    err = ""
    value = []

    # the arg array for the calculator should contain the
    # subnet label and a single availability zone that the subnet
    # should correspond to
    if (len(arg_array) == 2 and
        type(arg_array[0]) is str and
        type(arg_array[1]) is str):

        subnet_label = arg_array[0]
        az = arg_array[1]

    elif (len(arg_array) == 2 and
        type(arg_array[0]) is not str):

        err = ("The first argument should be a string that can be used " +
              "to search for the desired subnets (e.g. 'internal' or 'dmz')")

    elif (len(arg_array) == 2 and
        type(arg_array[1]) is not str):

        err = ("The second argument must be a single availability zone")

    elif len(arg_array) == 1:

        err = ("an availability zone must be included as a string " +
               "to calculate a subnet id")

    if not err:

        # see if a subnet id for this az has already been calculated
        cache_key = "subnet-id-%s-%s"%(subnet_label,az)
        value = check_calc_cache(params,cache_key,"")

        if not value:

            vpc, err = get_vpc(params)

            if not err:

                # get the subnet id with label and az provided
                subnet_ids,err = get_subnet_ids(vpc,
                                               [az],
                                                params,
                                                subnet_label)

                if len(subnet_ids)>1:
                    err = "more than one subnet was returned"
                elif len(subnet_ids)==1:
                    value =  subnet_ids[0]
                    cache_calc(params, cache_key, value)
                else:
                    err = "no subnets were returned for the label and zone provided"

    return value, err

def calc_base64_encoding(params,arg_array):

    encoded_string = ""
    err = ""

    # the arg array for the calculator should contain the
    # string to be encoded
    if (len(arg_array) == 1 and
         (type(arg_array[0]) is str or
          type(arg_array[0]) is str) ) :

        to_encode = arg_array[0]

    elif (len(arg_array) == 1 and
          type(arg_array[0]) is not str and
          type(arg_array[0]) is not str ):

        err = ("The first argument should be a string that is to be encoded")

    elif len(arg_array) == 0:

        err = "you need to include the string to be encoded"

    if not err:

        encoded_bytes = base64.b64encode(bytes(to_encode,"utf-8"))
        encoded_string = encoded_bytes.decode("utf-8")

    return encoded_string, err

def calc_int(params,arg_array):

    integered = ""
    err = ""

    # the arg array for the calculator should contain the
    # string to be encoded
    if (len(arg_array) == 1 and
         (type(arg_array[0]) is str or
          type(arg_array[0]) is str) ) :

        to_encode = arg_array[0]

    elif (len(arg_array) == 1 and
          type(arg_array[0]) is not str and
          type(arg_array[0]) is not str ):

        err = ("The first argument should be a string turned into an int")

    elif len(arg_array) == 0:

        err = "you need to include the string to be integered"

    if not err:

        integered = int(to_encode)

    return integered, err

def get_vpc(params):

    value = None
    err = ""

    value = check_calc_cache(params,"vpc",{})

    if not value:

        # get all vpcs
        vpcs,err = get_vpcs(params)

        if not err:

            # there should be only 1 vpc per v2 account
            if len(vpcs)>1:
                err = "more than 1 vpc found"

            elif len(vpcs)==0:
                err = "vpc not found"

            else:
                value = vpcs[0]
                cache_calc(params,"vpc", value)

    return value, err

def check_calc_cache(params,cache_key,default_value=""):
    # use the params as a means of caching calculate values
    # such that expensive aws queries can be minimized

    calc_cache = params.get("calc-cache",{})

    if calc_cache and cache_key  in calc_cache:
        return calc_cache[cache_key]
    else:
        return default_value

def cache_calc(params, cache_key, value):

    calc_cache = params.get("calc-cache",{})

    calc_cache[cache_key] = value

    params.set("calc-cache", calc_cache)

def clear_calc_cache(params):

    params.set("calc-cache",{})

