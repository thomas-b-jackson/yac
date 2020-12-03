import jmespath

def search(path, params, default_value=""):

    value = jmespath.search(path, params)

    if (type(value) != bool and value):
        return value
    elif type(value) == bool:
    	return value
    else:
        return default_value
