import sys, json, os, imp, getpass
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.module import get_module
from yac.lib.search import search
from yac.lib.paths import get_home_dump_path
from yac.lib.schema import validate
from yac.lib.params import Params
from yac.lib.input import Input

USER_INPUTS_PARAM_KEY = "UserInputs"

class InputsCacher():

    def __init__(self,
                 serialized_inputs_cacher):

        validate(serialized_inputs_cacher, "yac/schema/inputs_cacher.json")

        self.enabled = search("enabled",serialized_inputs_cacher,False)
        self.path = search("path",serialized_inputs_cacher,"")
        self.exclusions = search('"exclusions"',serialized_inputs_cacher,[])

    def get_path(self, params):

        # default cache path
        cache_path = ""

        if self.enabled and not self.path:

            cache_path_base = get_home_dump_path(params.get('service-alias'))
            cache_path=os.path.join(cache_path_base,"params.json")

        elif self.enabled and type(self.path) is dict:
            # render intrinsics in the cache path
            # note: this allows dynamic params like 'env' to be used as a pivot
            #   on the location of the cache file
            cache_path = apply_intrinsics(self.path,
                                          params)

        elif self.enabled and type(self.path) is str:
            cache_path = self.path

        return cache_path

    def is_enabled(self):
        return self.enabled

    def get_exclusions(self):
        return self.exclusions

    def __str__(self):
        to_ret = ""
        to_ret = to_ret + "enabled: %s\n"%self.enabled
        to_ret = to_ret + "path: %s\n"%self.path
        to_ret = to_ret + "exclusions: %s\n"%self.exclusions

        return to_ret

class Inputs():

    def __init__(self,
                 serialized_input_array,
                 inputs_cacher=None):

        """ Provides a species of stack params that are input interactively
            via command line prompts. Inputs are typically used when a service
            provider wants to create an easy installation experience for their
            service.

        Args:
            serialized_input_array: dictionary satisfying the yac/schema/input.json schema
            inputs_cacher: An instance of InstanceCacher

        Returns:
            None

        Raises:
            ValidationError: if the serialized_input_array fails schema validation or if any
                             individual input fails

        """

        self.inputs_cacher = inputs_cacher

        self.standard = []
        self.conditional = []

        for serialized_input in serialized_input_array:

            if 'conditions' in serialized_input:
                self.conditional.append(Input(serialized_input))
            else:
                self.standard.append(Input(serialized_input))

    def add(self, inputs):

        if inputs.standard:
            self.standard = self.standard + inputs.standard
        if inputs.conditional:
            self.conditional = self.conditional + inputs.conditional

    def load(self, params):
        """ Process inputs and load results into params

        Args:
            params: A Params instance

        Returns:
            None

        Raises:
            None

        """

        if self.inputs_cacher and self.inputs_cacher.is_enabled():

            if self.inputs_cacher.get_exclusions():

                # gather any inputs that aren't cachable
                # note: a classic example is the 'env' parameter
                no_cache_inputs = self.get_inputs(params,
                                                  self.inputs_cacher.get_exclusions())

                # add these to params
                params.add(no_cache_inputs)

            # load inputs that were cached on previous runs
            self._load_inputs_from_cache(params)

        # process all inputs and load them into params
        params_from_inputs = self.get_inputs(params)

        # add these to params
        params.add(params_from_inputs)

        if self.inputs_cacher and self.inputs_cacher.is_enabled():

            # cache any inputs collected
            self._cache_inputs(params, params_from_inputs)

    def get_inputs(self, params, these_input_keys=[]):

        params_input = Params({})

        # for each standard input
        for standard_input in self.standard:

            param_key = standard_input.get_key()

            # if we should gather all inputs (i.e. no specific input keys were
            # specified), or
            # if this param keys is one of the specific keys to be
            # gathered
            if ( not these_input_keys or
                 param_key in these_input_keys ):

                # handle this input
                value, user_prompted = standard_input.process(params)

                # accumulate this input
                if user_prompted:

                    params_input.set(param_key,
                                     value,
                                     standard_input.get_help())

                    params.add(params_input)

        # for each conditional input
        for conditional_input in self.conditional:

            param_key = conditional_input.get_key()

            # if we should gather all inputs (i.e. no specific input keys were
            # specified), or
            # if this param keys is one of the specific keys to be
            # gathered
            if ( not these_input_keys or
                 param_key in these_input_keys ):

                # handle this input
                value, user_prompted = conditional_input.process(params)

                # accumulate this input
                if user_prompted:

                    params_input.set(param_key,
                                     value,
                                     conditional_input.get_help())

        return params_input

    def _load_inputs_from_cache(self, params):

        cache_path = self.inputs_cacher.get_path(params)

        print("cache path is %s"%cache_path)

        root_path = self._get_params_cache_root_path(params)

        full_cache_path = os.path.join(root_path,cache_path)

        # user may have specified a params file as a command line arg
        if full_cache_path and os.path.exists(full_cache_path):

            print("loading auto-cached inputs from %s"%full_cache_path)

            params_str = self._get_file_contents(params, full_cache_path)

            params.add(Params(json.loads(params_str)))

    def _get_file_contents(self, params, file_rel_path):

        file_contents = ""
        root_path = self._get_params_cache_root_path(params)
        # if file exists relative to the servicefile path
        params_full_path = os.path.join(root_path,file_rel_path)
        if os.path.exists(params_full_path):

            with open(params_full_path) as file_arg_fp:
                file_contents = file_arg_fp.read()

        return file_contents


    def _cache_inputs(self, params, params_from_inputs):

        """ Ensure values input are represented in a prescribed cached input
             file so user doesn't have to re-enter them in future service updates

        Args:
            params: A Params instance containing all service params
            params_from_inputs: A Params instance representing parameters
                                gathered during inputs processing

        Returns:
            None

        Raises:
            None
        """

        if params_from_inputs:

            cache_path = self.inputs_cacher.get_path(params)

            # serialize the params object into a dictionary
            user_inputs_dict = params_from_inputs.serialize()

            # read in the current state of the cache
            cache_contents_str = self._get_file_contents(params, cache_path)

            if cache_contents_str:
                cache_contents_dict = json.loads(cache_contents_str)

                # add cached inputs
                user_inputs_dict.update(cache_contents_dict)

            # save the inputs back to the cache
            self._dump_serialized_params(params,
                                         user_inputs_dict,
                                         cache_path)

    def _dump_serialized_params(self, params, serialized_params, file_path):

        file_contents = ""

        if not os.path.isabs(file_path):
            root_path = self._get_params_cache_root_path(params)
            # if file exists relative to the servicefile path
            params_full_path = os.path.join(root_path,file_path)
        else:
            params_full_path = file_path

        # create the directory if it does not alread exist
        params_file_dir = os.path.dirname(params_full_path)
        if not os.path.exists(params_file_dir):
            os.makedirs(params_file_dir)

        print("caching inputs to %s"%params_full_path)
        with open(params_full_path, 'w') as the_file:
            the_file.write(json.dumps(serialized_params,indent=2))

    def _get_params_cache_root_path(self,params):

        root_path = ""

        # if the servicefile path exists, use that as the root path
        servicefile_path = params.get("servicefile-path")

        if servicefile_path:
            root_path = servicefile_path

        else:

            # use the .yac directory under the users home dir
            home = os.path.expanduser("~")

            service_name = params.get("service-name","")

            root_path = os.path.join(home,'.yac', service_name)

        return root_path
