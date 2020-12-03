import json, getpass
from yac.lib.stacks.aws.utils import get_ami
from yac.lib.version import return_latest
from yac.lib.naming import get_resource_name
from yac.lib.calcs import do_calc as do_calc_ext

def do_calc(calc_arg, params):
	""" determine the id of the ami corresponding to an
	    ami name

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

	ami_name,err = do_calc_ext(["lib/calc_ami_name.py"],params)

	# search for ami with this name
	ami_list = get_ami(ami_name)

	if ami_list and len(ami_list)==1:

		ami_id = ami_list[0].id

	elif not ami_list:
		err = "no AMIs are available corresponding to name: '%s'"%ami_name

	elif len(ami_list)>1:
		err = "more than one AMI is available corresponding to name: '%s'"%ami_name

	return ami_id, err