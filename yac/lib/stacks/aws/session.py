import os, boto3
from yac.lib.stacks.aws.paths import get_credentials_path

# keys for params used for session definition
PROFILE_KEY="profile"
ASSUME_ROLE_KEY="assume-role-arn"
REGION_KEY="region"
DESKTOP_KEY="desktop"

def get_session(params):
    # create a new boto3 session
    # args:
    #   params: yac.lib.params.Params instance
    # returns:
    #   boto3.Session

    # the creation of a session depends on build context,
    # including:
    #   the region
    #   the credentials profile (for desktop-based builds)
    #   the iam role to assume (for server-based builds)

    # creds created by yac use the 'default' profile for the default
    # set of credentials in a user's aws creds file
    profile = params.get(PROFILE_KEY,"default")

    # default region for nordstrom is us-west-2
    region = params.get(REGION_KEY,"us-west-2")

    # in build pipelines, build servers may need to assume a specific
    # iam role to perform builds in the aws account associated with the
    # role
    assume_role_arn = params.get(ASSUME_ROLE_KEY)

    # the desktop param tells yac if a build is happening on a dev desktop
    # vs. a build server
    desktop = params.get(DESKTOP_KEY)

    session = None
    err = ""

    creds_file_exists = os.path.exists(get_credentials_path())

    # if the build context is a developer desktop
    if desktop and creds_file_exists:

        try:
            if region:
                session = boto3.Session(profile_name=profile,
                                        region_name=region)
            else:
                session = boto3.Session(profile_name=profile)

        except botocore.vendored.requests.exceptions.ConnectionError as e:
            err = "There is a problem with your AWS security token. Renew using 'yac creds $SF <key>'"

    elif desktop and not creds_file_exists:

        err = "AWS sessions require an aws credentials file. Create using 'yac creds $SF <key>'"

    else:

        # instead assume we are running on an ec2 instance where
        #   aws access permissions are via an IAM role
        if region:
            session = boto3.Session(region_name=region)
        else:
            session = boto3.Session()

        # aws access can be based on current role of the EC2 or
        #   can instead be based on an assumed role
        if assume_role_arn:

            # use sts to get tokens associated with the desired role
            client = session.client("sts")
            creds = client.assume_role(RoleArn=assume_role_arn,
                                       RoleSessionName="build-session",
                                       DurationSeconds=3600)

            # create a session based on the creds returned
            if 'Credentials' in assumed_role_creds:
                session = boto3.Session(aws_access_key_id=creds['AccessKeyId'],
                                        aws_secret_access_key=creds['SecretAccessKey'],
                                        aws_session_token=creds['SessionToken'])

            else:

                err = "could not assume role associated with arn %s"%assumed_role_arn

    return session,err
