import os, shutil, re, json, copy
from yac.lib.file import get_file_contents, get_file_type, localize_file
from yac.lib.intrinsic import apply_intrinsics as apply_intrinsics_ext
from yac.lib.calcs import do_calc

TEMPLATE_ERROR_KEY = 'intrinsic-errors'

class TemplateError(Exception):
    pass

def apply_stemplate(string_w_instrinsics, params):

    """ Replaces template variables in a string with values in params

    Args:
        string_w_instrinsics: A string with yac-ref and yac-calc instrinsics in mustaches
        params: A Params instance

    Returns:
        A string with mustaches replaced with values.

    Raises:
        TemplateError: if string contains variables not defined in params
    """
    to_ret = ""

    yac_ref_arg_array =  get_intrinsic_mustaches("yac-ref",string_w_instrinsics)
    yac_calc_arg_array = get_intrinsic_mustaches("yac-calc",string_w_instrinsics)

    # render yac references
    string_w_instrinsics = render_yac_refs(yac_ref_arg_array, string_w_instrinsics, params)

    # render yac calc
    string_w_instrinsics = render_yac_calcs(yac_calc_arg_array, string_w_instrinsics, params)

    # raise an TemplateError if any failures were encountered
    if get_failures(params):
        raise TemplateError(_pp_failures(params))
    else:
        to_ret = copy.copy(string_w_instrinsics)
        return to_ret

def get_intrinsic_mustaches(instrinsic_type, string_w_instrinsics):

    # use regex to look for yac intrinsics
    #   ^} excludes a closing 'stache
    # parens identify groups, so the instrinsic 'arg' should
    #   show up in the second group in each element in the match
    #   list array
    search_str = "(%s):([^}]+)"%instrinsic_type
    # (yac-calc):([\S\s]+[^}])

    match_list = re.findall(search_str,string_w_instrinsics)

    # match list is formatted as:
    # [('<intrinsic>','<intrinsic arg>'),('<instrinsic>','<intrinsic arg>')]
    # return the list of intrinsic args
    instrisic_arg_array = []
    for match_item in match_list:
        if len(match_item)==2:
            instrisic_arg_array.append(match_item[1])

    return instrisic_arg_array

def render_yac_refs(yac_ref_arg_array, string_w_instrinsics, params):

    for yac_ref in yac_ref_arg_array:

        param_value = params.get(yac_ref)

        if param_value:

            # if the variable value is a string, unicode or int, treat this as
            # a yac ref
            if (isinstance(param_value, str) or
                 isinstance(param_value, str) or
                  isinstance(param_value, int)):

                # replace the mustache with the string value contained in
                # the template varaible
                to_replace = "{{yac-ref:%s}}"%yac_ref
                replace_with = str(param_value)

                string_w_instrinsics = string_w_instrinsics.replace(to_replace,
                                                                replace_with)

            else:
                # add a reference failure
                reference_failure(params,"%s is not a string or int"%yac_ref)

        else:

            # add a reference failure
            reference_failure(params,"%s is not defined"%yac_ref)

    return string_w_instrinsics

def render_yac_calcs(yac_calc_arg_array, string_w_instrinsics, params):

    for yac_calc_arg in yac_calc_arg_array:

        err = ""
        yac_calc_arg_list = []

        # each arg should be a serialized array. deserialize
        try:
            yac_calc_arg_list = json.loads(yac_calc_arg)
        except ValueError as e:
            err = e

        calc_value = ""
        if not err:
            # perform the calc
            calc_value, err = do_calc(yac_calc_arg_list,params)

        if calc_value and not err:

            # if the variable value is a string or a unicode, treat this as
            # a yac ref
            if (isinstance(calc_value, str) or
                isinstance(calc_value, str)):

                # replace the mustache with the string value contained in
                # the template varaible
                to_replace = "{{yac-calc:%s}}"%yac_calc_arg
                replace_with = str(calc_value)

                string_w_instrinsics = string_w_instrinsics.replace(to_replace,
                                                                    replace_with)

            else:
                # add a reference failure
                reference_failure(params,"calc %s does not return a string"%yac_calc_arg)

        elif err:

            # add a calc failure
            reference_failure(params,"calc %s returned the following error: %s"%(yac_calc_arg,err))

        elif not err and not calc_value:

            # add a calc failure
            reference_failure(params,"calc %s is not defined"%yac_calc_arg)

    return string_w_instrinsics

def apply_ftemplate(file_w_variables, params):

    """ Replaces template variables in a string with values in params

    Args:
        file_w_variables: A file with variables in mustaches
        params: A Params instance

    Returns:
        A string with mustaches replaced with values.

    Raises:
        TemplateError: if file does not exist, or
                       if file contains variables not defined in params
    """

    # read file into string
    string_w_instrinsics = get_file_contents(file_w_variables)

    return apply_stemplate(string_w_instrinsics, params)

def apply_templates_in_file(file_w_variables,
                            params,
                            rendered_file_dest="tmp"):

    """ Replaces template variables in a string with values in params

    Args:
        file_w_variables: A file with variables in mustaches
        params: A Params instance
        rendered_file_dest: The relative path to where the rendered file should be placed

    Returns:
        The path to a file with mustaches replaced with values.

    Raises:
        TemplateError: if source file does not exist
    """

    # get the file type
    file_abs_path = localize_file(file_w_variables,
                                  params.get('servicefile-path'))

    file_type = get_file_type(file_abs_path)

    # if the file is a text file render any variables in the file contents using the
    # provided template variables
    if (file_type and
            len(file_type) >= 1 and
            ('text' in file_type or
             'json' in file_type or
             'xml' in file_type or
             'html' in file_type)):

        # read file into string
        file_contents = get_file_contents(file_abs_path)

        # if the file is json, first attempt to render using intrinsics instead of templates
        rendered_file_contents = ""

        if 'json' in file_type:

            rendered_file_contents = apply_intrinsics(file_contents, params)

        else:
            # render template variables
            rendered_file_contents = apply_stemplate(file_contents, params)

        # create the directory to hold the rendered file contents
        if not os.path.exists(rendered_file_dest):
            os.makedirs(rendered_file_dest)

        file_name = os.path.basename(file_w_variables)

        rendered_file = os.path.join(rendered_file_dest, file_name)


        # write the rendered string into the temp file
        with open(rendered_file, 'w') as outfile:
            outfile.write(rendered_file_contents)
    else:

        # this isn't a text file, so don't attemp to render any variables
        # instead copy from source to destination

        # create a 'tmp' directory to hold the files
        if not os.path.exists(rendered_file_dest):
            os.makedirs(rendered_file_dest)

        file_name = os.path.basename(file_w_variables)

        rendered_file = os.path.join(rendered_file_dest, file_name)

        # print "nrf: %s"%rendered_file

        shutil.copy(file_w_variables, rendered_file)


    return rendered_file

def apply_templates_in_dir(source_dir,
                           params,
                           dest_dir="tmp",
                           relative_path=True):

    """ Replaces template variables in all files in a directory with values in params

    Args:
        source_dir: A directory containing files with variables in mustaches
        params: A Params instance
        dest_dir: The relative path to where the rendered file should be placed

    Returns:
        The path to a directory with files with mustaches replaced with values.

    Raises:
        TemplateError: if the directory does not exist
    pass
.
    """

    if relative_path:
        servicefile_path = params.get('servicefile-path')
        source_full_path = os.path.join(servicefile_path, source_dir)
    else:
        source_full_path = source_dir

    if os.path.exists(source_full_path):

        # print "rendering files under %s"%(source_full_path)

        # get the contents of this directory
        dir_children = os.listdir(source_full_path)

        for this_child in dir_children:

            if os.path.isfile(os.path.join(source_full_path, this_child)):

                this_file = os.path.join(source_full_path, this_child)

                # print "rendering %s"%this_file

                # split off the servicefile portion
                apply_templates_in_file(this_file, params, dest_dir)

            else:

                # this item is a directory

                # destination is relative to the current destination
                new_dest_dir = os.path.join(dest_dir, this_child)

                # source dir is relative to the current source
                new_source_dir = os.path.join(source_full_path, this_child)

                apply_templates_in_dir(new_source_dir, params, new_dest_dir)

    else:
        raise TemplateError("path %s does not exist"%source_full_path)

def apply_intrinsics(file_contents, params):

    rendered_file_contents = ""

    file_dictionary = json.loads(file_contents)

    rendered_file_dictionary = apply_intrinsics_ext(file_dictionary,params)

    if rendered_file_dictionary:
        # print("to dump: %s, type: %s"%(rendered_file_dictionary,type(rendered_file_dictionary)))
        rendered_file_contents = json.dumps(rendered_file_dictionary,indent=2)
    else:
        rendered_file_contents = None

    return rendered_file_contents

def reference_failure(params, ref_value, failure_msg=""):

    # see if this reference failure has already been reported
    if not _reference_failure_reported(params,ref_value):
        # add to list of failures
        _add_failure(params, 'yac-ref', ref_value)

def _reference_failure_reported(params, ref_value):

    setpoint = '%s: %s'%('yac-ref', ref_value)
    error_list = get_failures(params)

    return setpoint in get_failures(params)

def _add_failure(params, error_type, failure_msg):

    # secret load failed. add to list of errors
    setpoint = '%s: %s'%(error_type, failure_msg)
    error_list = get_failures(params)
    params.set(TEMPLATE_ERROR_KEY,error_list+[setpoint])

def get_failures(params):

    return params.get(TEMPLATE_ERROR_KEY,[])

def _pp_failures(params):

    error_list = get_failures(params)

    print("The following template failures were recorded:")
    for item in error_list:
        print(item)