import requests, jmespath

# for the registry find, find the latest version of the app input, in the container org input
def get_latest_version(app, container_org, registry_url='https://registry.hub.docker.com'):

    # endpoint use to determine the latest version in the registry input for this app
    endpoint_uri = "/v2/repositories/%s/%s/tags"%(container_org,app)

    # hit the endpoint
    endpoint_response = requests.get(registry_url + endpoint_uri) 

    # use jmespath to extract just the version value for each
    versions = jmespath.search("results[*].name",endpoint_response.json())

    # jmespath leaves a weird prefix on each result. remove by str conversion
    latest_version = "not found!"

    if versions:

        versions = [str(i) for i in versions]

        latest_version = ""

        if (versions and len(versions)>=1):

            if 'latest' in versions:

                latest_version = "latest"
            
            else:
                
                # sort and grab the last value in the resulting list (the latest version)
                versions.sort()
                latest_version = versions[-1]

    return str(latest_version)

def get_app_version(app_alias, my_service_descriptor):

    app_version = ""

    # the version would be in the image for this app
    search_str = "task-definition.containerDefinitions[?name=='%s'].image"%app_alias
    images_found = jmespath.search(search_str, my_service_descriptor)

    if images_found and len(images_found)==1:

        # grab the version from the tail end of the image label
        app_version = str(images_found[0]).split(':')[-1]

    return app_version    

# @param version1, a string, e.g. 1.2.1
# @param version2, a string
# @returns version 1 or version2, whichever is the latest
def return_latest(version1, version2):

    v1, v2 = version1.split("."), version2.split(".")
    
    if len(v1) > len(v2):
        v2 += ['0' for _ in range(len(v1) - len(v2))]
    elif len(v1) < len(v2):
        v1 += ['0' for _ in range(len(v2) - len(v1))]
    
    latest = ""
    i = 0
    while i < len(v1):
        if (v1[i].isdigit() and v2[i].isdigit() and
            int(v1[i]) > int(v2[i]) ):
            latest = version1
            break
        elif (v1[i].isdigit() and v2[i].isdigit() and
            int(v1[i]) < int(v2[i]) ):
            latest = version2
            break
        else:
            i += 1
    
    return latest

# @param version1, a string, e.g. 1.2.1
# @param version2, a string
# @returns True if both versions are the same, False o.w.
def is_same(version1, version2):

    v1, v2 = version1.split("."), version2.split(".")
    
    if len(v1) > len(v2):
        v2 += ['0' for _ in range(len(v1) - len(v2))]
    elif len(v1) < len(v2):
        v1 += ['0' for _ in range(len(v2) - len(v1))]
    
    same = True
    i = 0
    while i < len(v1):
        if (v1[i].isdigit() and v2[i].isdigit() and
            int(v1[i]) == int(v2[i]) ):
            same = same and True
        else:
            same = same and False
        i += 1
    
    return same    

# @param version1, a string, e.g. 1.2.1
# @param version2, a string
# @returns True if version 1 is later than version2, False o.w.
def is_first_arg_latest(version1, version2):

    version = return_latest(version1, version2)    
    
    if version == version1:
        return True
    elif version == version2:
        return False
    else:

        return False        

def is_a_version(version):

    v1 = version.split(".")

    is_version = True
    i=0
    while i < len(v1):

        if not v1[i].isdigit():
            is_version = False
            break
        else:
            i += 1 

    return is_version    