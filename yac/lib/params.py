import os, json, jmespath, copy
from yac.lib.schema import validate

class Params():

    def __init__(self,
                 serialized_params):

        """ Service parameters are key/value pairs used for rendering
            template variables. When serialized, params must satisfy the
            schema: "yac/schema/params.json"

        Args:
            serialized_params: A dictionary of serialized parameters
            params_file: A file containing serialized parameters
            kvp_str: A string containing parameters in key/value pairs,
                     formatted as 'key1:value1,key2:value2,...'

        Returns:
            A Params instance

        Raises:
            IntrinsicsError: raised if serialized_params contain yac instrincs,
                             and if any of the instrinsics failed to render


        A typical serialized param looks like:

        ...
        "some-param-key: {
            "comment": "an explanation of this parameter",
            "value": "param-value"
        }
        ...

        A parameter can then be referenced in another dictionary by
        an intrinsic as:

        ...
        {
            "item1": "non-intrinsic",
            "item2": {"yac-ref": "some-param-key"}
        }
        ...

        Altenatively, a parameter can be referenced in a test file using
        mustaches, as:

        ...
            <db-config>{{some-param-key}}</db-config>
        ...

        Parameters can contain other intrinsics for values, e.g.:

        ...
        "some-param-key: {
            "comment": "an explanation of this parameter",
            "value": {"yac-calc": ["/lib/my_calculator.py"]}
        }
        ...


        """

        # validate params. this will raise a validation error if
        # params don't satisfy the schema
        # validate(serialized_params, "yac/schema/params.json")

        self.values = serialized_params

    def keys(self):
        return list(self.values.keys())

    def add(self, params):

        self.values.update(params.values)

    def set(self, param_key, value, comment="", value_key='value'):

        self.values[param_key] = {value_key : value, 'comment': comment}

    def get(self, param_key, default_value="", value_key='value'):

        value = default_value

        if (param_key in self.values and value_key in self.values[param_key] and
            'lookup' in self.values[param_key]):

            # this is a map lookup
            value = self._map_get(param_key, default_value, value_key)

        elif param_key in self.values and value_key in self.values[param_key]:
            # this is a normal lookup
            value = self.values[param_key][value_key]

        return value

    def serialize(self):
        return self.values

    def _map_get(self, map_key, default_value="", value_key='value'):

        value = default_value

        if (map_key in self.values and value_key in self.values[map_key] and
            'lookup' in self.values[map_key]):

            # get the lookup
            lookup = self.values[map_key]["lookup"]

            # treat the lookup as a key
            param_val = self.get(lookup,"")

            if ( param_val and
                 (map_key in self.values) and
                 (value_key in self.values[map_key]) and
                 (param_val in self.values[map_key][value_key]) ):

                value = self.values[map_key][value_key][param_val]

        return value

    def load_kvps(self,kvps_str):

        kvp_array = kvps_str.split(",") if kvps_str else []

        for kvp in kvp_array:
            kcv = kvp.split(":")

            # each key value could include an optional comment
            if len(kcv)==2:
                self.set(kcv[0],kcv[1])

            if len(kcv)==3:
                self.set(kcv[0],kcv[1],kcv[2])

    def load_from_file(self, params_file_arg):

        params_str = ""

        # user may have specified a params file as a command line arg
        if params_file_arg and os.path.exists(params_file_arg):

            params_str = get_file_contents(params_file)

            serialized_params = json.loads(params_str)

            # validate
            validate(serialized_params,"yac/schema/params.json")

            self.values.update(Params(serialized_params))

    def load_from_env_variables(self):

        # the DESKTOP env variable is used to signal that yac is running on
        # a developer desktop (as opposed to a build server).
        if "DESKTOP" in os.environ:
            desktop = bool(os.environ["DESKTOP"])
        else:
            desktop = False
        msg = ("is yac currently running on a developer desktop (vs a build server)?" +
               " Note: this can be overridden via the DESKTOP environment variable")

        self.set('desktop', desktop, msg)

    def _get_file_contents(self, file_rel_path):

        file_contents = ""
        root_path = self._get_params_cache_root_path()
        # if file exists relative to the servicefile path
        params_full_path = os.path.join(root_path,file_rel_path)
        if os.path.exists(params_full_path):

            print("loading params from %s"%params_full_path)

            with open(params_full_path) as file_arg_fp:
                file_contents = file_arg_fp.read()

        return file_contents

    def __str__(self):
        return json.dumps(self.values,indent=2)
