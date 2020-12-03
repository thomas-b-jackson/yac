import os, imp, urllib.parse, copy
from yac.lib.file import get_localized_script_path, load_dict_from_file, get_file_contents
from yac.lib.naming import get_resource_name
from yac.lib.calcs import do_calc
from yac.lib.module import get_module
from yac.lib.schema import validate

INSTINSICS = ['yac-ref', 'yac-join', 'yac-fxn', 'yac-name', 'yac-calc','yac-include']
YAC_REF_ERROR = "ref-error"
YAC_FXN_ERROR = "fxn-error"
INSTRINSIC_ERROR_KEY = 'intrinsic-errors'

class IntrinsicsError(Exception):
    pass

def apply_intrinsics(source_dict, params):

    """ Replaces yac intrinsics in a dictionary

    Args:
        source_dict: A dictionary with intrinsics
        params: A Params instance

    Returns:
        A dictionary with yac intrinsics replaced with values

    Raises:
        IntrinsicsError: message includes what instrinsics failed to render


    Currently supported instrisics include:

    {"yac-ref": "<param key>"}
        where,
           <param-key> is the key of a parameter to be dereferenced

    {"yac-join": ["<delimitter>", [elem1, elem2, ...,elemN]]}
        where,
           <delimitter> is the delimitter to be placed between each element
           <elem1-N> are any object (including another intrinsic)

    {"yac-name": "<resource>"}

        where,
            <resource> is an arbitrary string that helps define the
            resource (i.e. "elb", "asg", "stack", etc.)

        the 'name' instrinsic is a short-hand form of the 'join'
        intrinsic, since resource naming is such a common occurrence in
        stack templates. by default, it appends the service alias with the
        resource label, separated by a '-' delimmter.

        this default convention can be overridden via service-supplied
        'naming-convention' parameter, formatted as:

        ...
        "naming-convention": {
            "comment": "name resources using the alias followed by the environment",
            "value": {
                "param-keys": ['service-alias','env'],
                "delimitter": "-"
            }
        }
        ...
    }

    {"yac-include": <arg>}
        where <arg> is either:
            * a relative path to a json or yaml file containing a stack resource, or
            * a relative path to a python module with a 'generate_resource()' fxn

    {"yac-calc": <argv>}
        where,
            <argv> is an argv-style array containing the calculator to
            run and any arguments to pass to the calculator. Each element
            in argv is comma separated.

        the following 'stock'calculators are available:

        - {"yac-calc": ["vpc-id"]},

            which calculates the id of the vpc associated with the
            current aws credential

        - {"yac-calc": ["vpc-cidr"]},

            which calculates the cidr of the vpc associated with the
            current aws credential

        - {"yac-calc": ["subnet-ids","<label-str>",[<availability-zones>]],

            which calculates the subnets ids for all subnets in the vpc
            associated with the current aws credential. subnet ids
            returned are per the order of zones in the [<availability-zones>]
            array.

        In addition to the stock calculators, the yac-calc intrinsic will
        accept a path to any service-supplied module that contains a 'do_calc()'
        method, as:

        - {"yac-calc": ["<path to module>","arg1","arg2", etc.]},

            an example might look like:
               {"yac-calc": ["/lib/foo.py","bar1","bar2"]}

            the foo module is loaded, and its do_calc() function is called as:
                do_calc(["bar1", "bar2"])

            note: the module path is relative to the servicefile.

    """

    # make sure input is in the expected object format
    validate(source_dict,'yac/schema/intrinsics_input.json')

    # Take a copy of template before applying intrinsics.
    source_dict_copy = copy.deepcopy(source_dict)

    # source_dict can contain intrinsics at any level.
    # _apply_intrinsics() uses recursion in processing intrinsics, and thus does not
    # support intrinsics at the first-child level. to address, do the following:
    # 1) create a placeholder first child that keys the source_dict
    # 2) process using _apply_intrinsics()
    # 3) return the rendered dictionary under placeholder

    placeholder_key = "placeholder"
    placeholder_dict = {placeholder_key: source_dict_copy}

    rendered_dictionary = _apply_intrinsics(placeholder_dict, params)

    # raise an IntrinsicsError if any failures were encountered
    if get_failures(params):
        raise IntrinsicsError(_pp_failures(params))
    else:
        return rendered_dictionary[placeholder_key]


def _apply_intrinsics(source_dict, params):

    """ Replaces yac intrinsics in a dictionary.
        Collects load failures as it goes and saves
        them in a param value with key INSTRINSIC_ERROR_KEY

    Args:
        source_dict: A dictionary with intrinsics
        params: A Params instance

    Returns:
        A dictionary with yac intrinsics replaced with values.

    Raises:
        None
    """

    for key in list(source_dict.keys()):

        if type(source_dict[key])==dict:
            source_dict[key] = _apply_intrinsics_dict(source_dict[key], params)

        elif type(source_dict[key])==list:
            source_dict[key] = _apply_intrinsics_list(source_dict[key], params)

        else:
            source_dict[key] = _apply_intrinsics_leaf(key,source_dict, params)

    return source_dict

def _apply_intrinsics_dict(source_dict, params):

    sub_keys = list(source_dict.keys())
    if len(set(sub_keys) & set(INSTINSICS))==1:
        # treat this as a leaf
        source_dict = _apply_intrinsics_leaf(sub_keys[0],source_dict, params)
    else:
        source_dict = _apply_intrinsics(source_dict,params)

    return source_dict

def _apply_intrinsics_list(source_list, params):

    for i, item in enumerate(source_list):
        if type(item) is dict:
            source_list[i] = _apply_intrinsics_dict(item, params)
        elif type(item) is list:
            source_list[i] = _apply_intrinsics_list(item, params)
        else:
            source_list[i] = item
    return source_list

def _apply_intrinsics_leaf(key, source_dict, params):

    # see if any of the values have intrinsics
    if key == 'yac-ref':

        # Pull referenced value from the params. Default to a string
        # containing an error message in case the reference does not have
        # a corresponding value.

        # apply any intrinsics in the reference
        #rendered_ref_args = _apply_intrinsics_list(source_dict[key], params)

        setpoint = params.get(source_dict[key],"M.I.A.")
        if setpoint=="M.I.A.":
            reference_failure(params, source_dict[key])

        return setpoint

    if key == 'yac-calc':

        # make sure arg is a list
        if type(source_dict[key]) is not list:
            msg = "%s\n%s"%(source_dict[key],"argument to yac-calc must be type list")
            calc_failure(params, msg)
            setpoint=""
        else:
            # apply any intrinsics in the calc arguments
            rendered_calc_args = _apply_intrinsics_list(source_dict[key],params)

            setpoint,err = do_calc(rendered_calc_args,params)

            if err:
                msg = "%s\n%s"%(source_dict[key],err)
                calc_failure(params, msg)

        return setpoint

    elif key == 'yac-join':

        delimiters = source_dict[key][0]
        name_parts = source_dict[key][1]

        # apply intrinsics in the list of items to be joined
        filled_parts = _apply_intrinsics_list(name_parts, params)

        # get rid of empty strings before joining with delimitter
        filled_parts = [_f for _f in filled_parts if _f]

        return delimiters.join(filled_parts)

    elif key == 'yac-fxn':

        # this value should be filled by custom function supplied by service
        fxn_script = source_dict[key]
        return apply_custom_fxn(fxn_script, params)

    elif key == 'yac-name':

        # get the name for this resource
        resource = source_dict[key]
        return get_resource_name(params, resource)

    elif key == 'yac-include':

        # pull the templates out of the included file
        included_file = source_dict[key]
        servicefile_path = params.get('servicefile-path')
        included_dict = {}
        include_err = ""

        if get_file_contents(included_file, servicefile_path):

            # attempt to load the contents of the included file as a
            # dictionary
            included_dict,include_err = load_dict_from_file(included_file, servicefile_path)

            if not include_err:

                # render any intrisics in the included dictionary
                _apply_intrinsics(included_dict, params)

        else:
            include_err = "%s is either non-existant or has no content"%included_file

        # if any errors where generated in the inclusion processing,
        # register the error
        if include_err:
            include_failure(params,include_err)

        return included_dict

    else:

        return source_dict[key]

def apply_custom_fxn(script_path_arg, params):

    # get the python file that will be used to build this param value

    servicefile_path = params.get('servicefile-path')

    script_path = get_localized_script_path(script_path_arg, servicefile_path)

    return_val = ""

    if (script_path and os.path.exists(script_path)):

        # module_name = 'yac.lib.customizations.%s.params'%app_alias
        module_name = 'yac.lib.customizations'
        script_module = imp.load_source(module_name,script_path)

        # call the get_value fxn in the script
        return_val = script_module.get_value(params)

    else:
        fxn_failure(params,'function %s is missing'%(script_path))

    return return_val

def reference_failure(params, ref_value):

    # see if this reference failure has already been reported
    if not _reference_failure_reported(params,ref_value):
        # add to list of failures
        if ref_value:
            _add_failure(params, 'yac-ref', ref_value)
        else:
            _add_failure(params, 'yac-ref', "<missing param ref>")

def _reference_failure_reported(params, ref_value):

    setpoint = '%s: %s'%('yac-ref', ref_value)
    error_list = get_failures(params)

    return setpoint in get_failures(params)

def calc_failure(params, failure_msg):

    # secret load failed. add to list of errors
    _add_failure(params, 'yac-calc', failure_msg)

def fxn_failure(params, failure_msg):

    # secret load failed. add to list of errors
    _add_failure(params, 'yac-fxn', failure_msg)

def include_failure(params, failure_msg):

    # secret load failed. add to list of errors
    _add_failure(params, 'yac-include', failure_msg)

def get_failures(params):

    return params.get(INSTRINSIC_ERROR_KEY,[])

def _add_failure(params, error_type, failure_msg):

    # secret load failed. add to list of errors
    setpoint = '%s: %s'%(error_type, failure_msg)
    error_list = get_failures(params)
    params.set(INSTRINSIC_ERROR_KEY,error_list+[setpoint])

def _pp_failures(params):

    error_list = get_failures(params)

    print("The following yac intrinsics failed to render. Please correct and try again")
    for item in error_list:
        print(item)


