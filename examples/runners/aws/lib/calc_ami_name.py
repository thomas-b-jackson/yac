def do_calc(calc_arg, params):
	""" determine the name of the yac runner ami

    Args:
        calc_arg: should be an empty array for this calc
        params:  a Params instance

    Returns:
        ami_id: an string containing the the id of an ami
        err:  a string containing an error msg

    Raises:
        None

    """

	ami_id=""
	err=""

	# get alias and gitlab version
	service_alias = params.get("service-default-alias")
	gitlab_version = params.get('gitlab-version')

	ami_name = "-".join([service_alias,gitlab_version])

	return ami_name, err

