import json, getpass
from yac.lib.stacks.aws.utils import get_ami

def do_calc(calc_arg, params):
	""" determine the id of the ami corresponding to an ami name

    Args:
        calc_arg: should be an empty array for this calc
        params:  a Params instance

    Returns:
        ami_id: an string containing the the id of an ami
        err:  a string containing an error code

    Raises:
        None

    """

	ami_name = params.get('ami-name')

	ami_id=""
	err=""

	ami_list = get_ami(ami_name)


	if ami_list and len(ami_list)==1:

		ami_id = ami_list[0].id

	elif not ami_list:
		err = "no AMIs are available corresponding to ami: %s"%ami_name

	elif len(ami_list)>1:
		err = "more than one AMI is available corresponding to to ami: %s"%ami_name

	return ami_id, err