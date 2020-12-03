import os, json
from jsonschema import validate as schema_validate
from jsonschema import ValidationError as ExtValidationError
from yac.lib.paths import get_yac_path

def validate( object_dict, schema_rel_path ):
    """ Validate that a dictionary satisfies a json schema

    Args:
        object_dict: A dictionaray representing some object
        schema_rel_path: The path the schema that the object should satisfy

    Returns:
        None

    Raises:
        ValidationError.
    """

    schema, err = _load_schema( schema_rel_path )

    if not err:

        # only perform the validation against
        # a non-null dictionary
        if object_dict:

            try:
                schema_validate( object_dict, schema )
            except ExtValidationError as e:
                # provide some context before re-raising exception
                raise ExtValidationError(_pp_failures(e,schema))

    else:
        raise ExtValidationError(err)

def _load_schema( schema_relative_path ):

    dictionary = {}
    err = ""

    # get the full path to this module file
    # module_path = os.path.dirname(os.path.abspath(__file__))

    # split path based on '/yac/'
    # path_parts = module_path.split('/yac/')

    full_path = os.path.join(get_yac_path(),schema_relative_path)

    if os.path.exists(full_path):

        with open(full_path) as file_path_fp:

            file_contents = file_path_fp.read()

            dictionary = json.loads(file_contents)

    else:
        err = 'schema does not exist at relative path: %s'%schema_relative_path

    return dictionary, err

def _pp_failures(val_error,schema):

    err = ""

    print(json.dumps(val_error.schema,indent=2))

    err = err + "\nyac object: %s\n"%schema['title']
    err = err + "object description: %s\n"%schema['description']
    err = err + "object attribute: %s\n"%val_error.schema['title']
    err = err + "see usage examples by running: 'yac examples | grep %s'\n"%schema['title'].lower()
    err = err + "schema validation error is as follows ...\n%s"%str(val_error)

    return err