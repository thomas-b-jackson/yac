import sys, json, os, imp, getpass
from yac.lib.search import search
from yac.lib.schema import validate
from yac.lib.params import Params

USER_INPUTS_PARAM_KEY = "UserInputs"

class Input():

    def __init__(self,
                 serialized_input):

        """ Inputs are typically used when a service
            provider wants to create an easy installation experience for their
            service.

        Args:
            serialized_input: A dictionary containing serialized input,
                               satisfying the yac/schema/input.json schema

        Raises:
            ValidationError: if a inputs fails schema validation

        """

        validate(serialized_input, "yac/schema/input.json")

        self.key = search("key",serialized_input,"")
        self.type = search("type",serialized_input,"")
        self.title = search("description",serialized_input,"")
        self.help = search("help",serialized_input,"")
        self.required = search("required",serialized_input,True)
        self.options = search("options",serialized_input,[])
        self.conditions = search("conditions",serialized_input,{})

    def get_key(self):
        return self.key

    def get_help(self):
        return self.help

    def process(self, params):

        value=""
        user_prompted=False

        # if there are no conditions or all conditions are met ...
        if self.conditions_met(params):

            value, user_prompted = self.gather(params)

        return value, user_prompted


    def conditions_met(self, params):

        conditions_met = True

        # currently the only conditional supported is based on key-value pair (aka 'kvps')
        # conditions are met if the state of the conditional params matches the current params
        if self.conditions and 'kvps' in self.conditions:

            # load the kvps into params
            condition_params = Params({})
            condition_params.load_kvps(self.conditions['kvps'])

            for condition_param_key in list(condition_params.keys()):
                if params.get(condition_param_key) != condition_params.get(condition_param_key):
                    conditions_met = False
                    break

        return conditions_met

    def gather(self,params):

        value = ""

        # if the param is not yet defined
        if not params.get(self.key,''):

            # prompt user to provide a value for this param
            if self.type == "array":
                value = self.validate_array_input()
                user_prompted=True
            else:
                value = self.validate_input()
                user_prompted=True

        else:
            value = value = params.get(self.key,'')
            user_prompted = False

        return value,user_prompted

    def validate_input(self):
        # for injesting individual inputs

        # map input types to appropriate validation functions
        validation_fxn_map = {
            "int": "int_validation",
            "string": "string_validation",
            "password": "string_validation",
            "bool": "bool_validation",
            "path": "path_validation"
        }

        # load the name of the validation function
        # appropriate to this input type
        # (supported types enforced via inputs schema)
        validation_fxn_name = validation_fxn_map[self.type]

        validation_failed = True

        if self.required:
            param_msg = "\nThis service requires the following input: %s"%self.title
        else:
            param_msg = "\nThis service accepts the following optional input: %s"%self.title

        print(param_msg)
        print(self.help)

        if self.options:

            if len(self.options)>10:
                response = input("Press <enter> to see a list of availble options >> ")
                print("Choices include: \n%s"%pp_list(self.options))
            else:
                print("Choices include: \n%s"%pp_short_list(self.options))

        typed_input = None

        while validation_failed:

            if self.options:
                input_msg = "Please paste in one of the available options for %s >> "%self.title
            else:
                input_msg = "Please input a value for %s >> "%self.title

            if self.type != "password":
                response = input(input_msg)
            else:
                response = getpass.getpass(input_msg)

            response = response.strip("'")

            # validate the response
            validation_failed, typed_input = eval(validation_fxn_name)(response,
                                                    self.options,
                                                    self.required)

        return typed_input

    def validate_array_input(self):
        # for injesting arrays of inputs

        validation_failed = True
        array_building = True

        if self.required:
            param_msg = "\nThis service requires the following input: %s"%self.title
        else:
            param_msg = "\nThis service accepts the following optional input: %s"%self.title

        print(param_msg)
        print(pp_help(self.help))

        if self.options:

            response = input("Press <enter> to see a list of availble options >> ")
            print("Choices include: \n%s"%pp_list(self.options))

        print("Paste in values one at a time and press Enter ( press Enter when done ) ...")

        inputs = []

        while validation_failed:

            response = input("... input an item for '%s' >> "%self.title)

            if response:
                inputs.append(response)
            else:
                validation_failed,inputs = array_validation(inputs,
                                                            self.options,
                                                            self.required)

        return inputs

def string_validation(input,options,required,max_strlen=4000):

    validation_failed = False
    if options:

        if type(options[0])==dict:
            # pull out just the options values
            options = jmespath.search("[*].Option",options)

        if required and input not in options:
            validation_failed = True
            retry_msg = "Input invalid - please select from the available options"

    if max_strlen:
        if len(input)>max_strlen:
            validation_failed = True
            retry_msg = "Input invalid (too long) - please input a string with <= %s chars"%max_strlen

    if required and not input:
        validation_failed = True
        retry_msg = "Input required - please enter a value"

    if validation_failed:
        print(retry_msg)

    return validation_failed, input

def path_validation(input,options,required,max_strlen=4000):

    validation_failed = False
    if options:

        if input not in options:
            validation_failed = True
            retry_msg = "Input invalid - please select from the available options"

    if max_strlen:
        if len(input)>max_strlen:
            validation_failed = True
            retry_msg = "Input invalid (too long) - please input a string with <= %s chars"%max_strlen

    if required and not input:
        validation_failed = True
        retry_msg = "Input required - please enter a value"

    if not os.path.exists(input):
        validation_failed = True
        retry_msg = "Invalid path - please try again"

    if validation_failed:
        print(retry_msg)

    return validation_failed, input

def int_validation(input,options,required,max_value=sys.maxsize):

    validation_failed = False

    if options:
        if not input.isdigit(input) or int(input) not in options:
            validation_failed = True
            retry_msg = "Input invalid - please select from the available options"

    if max_value:
        if not input.isdigit() or int(input) > max_value:
            validation_failed = True
            retry_msg = "Input invalid - please input an int <= %s"%max_value

    if required and not input:
        validation_failed = True
        retry_msg = "Input required - please enter a value"

    if ( input and not input.isdigit() ):
        validation_failed = True
        retry_msg = "Input invalid - integers only"

    typed_input = None
    if validation_failed:
        print(retry_msg)
    else:
        typed_input = int(input)

    return validation_failed, typed_input

def bool_validation(input,options,required,optional_arg=""):

    validation_failed = (input not in ["True", "true", "False", "false"])

    if required and not input:
        retry_msg = "Input required - please enter a value"

    elif validation_failed:
        retry_msg = "Input invalid - true/false only"

    typed_input = None
    if validation_failed:
        print(retry_msg)
    else:
        typed_input = input in ["true", "True"]

    return validation_failed, typed_input

def input_validation(input,options,required,retry_msg):

    # attempt to find the vpc input
    validation_failed = input not in options

    if validation_failed:
        print(retry_msg)

    return validation_failed

def array_validation(inputs,options,required,arg=""):

    validation_failed = len(set(inputs) & set(options)) != len(inputs)

    if validation_failed:
        retry_msg = "Input invalid - please select from the available options"
        print(retry_msg)
        inputs=[]

    return validation_failed, inputs

def pp_list(list):
    str = ""
    for item in list:
        str = str + '* %s\n'%item

    return str

def pp_short_list(list):
    str = ""
    for item in list:
        str = str + ' %s'%item

    return "( %s )"%str

def pp_help(help):

    if type(help)==list:
        ret = pp_list(help)
    else:
        ret = str(help)

    return ret