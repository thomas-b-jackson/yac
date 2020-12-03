import os, json, yaml, boto3, botocore
from yac.lib.schema import validate
from yac.lib.search import search
from yac.lib.stacks.aws.paths import get_credentials_path
from yac.lib.vaults.file import FileVault
from yac.lib.stacks.aws.session import get_session

class S3Vault(FileVault):

    def __init__(self,
                 vault_configs={}):

        validate(vault_configs, "yac/schema/vaults/s3.json")

        self.vault_bucket = search('"bucket"', vault_configs)
        self.vault_s3_path = search('"vault-path"', vault_configs)
        self.format = search("format", vault_configs, "json")

        vault_file_local_path = get_vault_local_path(self.vault_bucket,
                                                     self.vault_s3_path)

        file_vault_config = {"vault-path": vault_file_local_path,
                             "format": self.format}

        FileVault.__init__(self,file_vault_config)

        self.session = None

    def initialize(self, params):

        err = ""

        # get a boto3 session
        self.session, err = get_session(params)

        if not err and self.session:

            vault_exists_bool = self.vault_exists()

            if vault_exists_bool:

                s3 = self.session.resource('s3')

                # pull file down to the local dir
                err = s3.meta.client.download_file(self.vault_bucket,
                                             self.vault_s3_path,
                                             self.vault_path)

                # load the file contents
                FileVault.initialize(self, params)

            else:
                err = "vault at %s does not exist"%self.vault_s3_path

    def get_type(self):
        return "s3"

    def update(self, file_contents):

        if self.session:

            s3 = self.session.resource('s3')

            # update contents of file vault
            FileVault.update(self, file_contents)

            # deserialize to s3 by uploading contents to s3
            s3.meta.client.upload_file(self.vault_path,
                                       self.vault_bucket,
                                       self.vault_s3_path)


    def deserialize(self, serialized_vault):
        # TODO: deprecate

        if self.session:

            s3 = self.session.resource('s3')

            # deserialize to file vault to update contents of file
            FileVault.deserialize(self, serialized_vault)

            # deserialize to s3 by uploading contents to s3
            s3.meta.client.upload_file(self.vault_path,
                                       self.vault_bucket,
                                       self.vault_s3_path)

    def __str__(self):
        ret = ("s3 path: s3://%s/%s\n"%(self.vault_bucket,self.vault_s3_path) +
               "local path: %s\n"%self.vault_path +
               "ready: %s\n"%self.ready +
               "data:\n %s\n"%self.vault)
        return ret

    def vault_exists(self):

        object_exists = False

        if self.session:
            s3 = self.session.resource('s3')
            bucket = s3.Bucket(self.vault_bucket)
            try:

                objs = list(bucket.objects.filter(Prefix=self.vault_s3_path))
                if len(objs) > 0 and objs[0].key == self.vault_s3_path:
                    object_exists = True

            except botocore.exceptions.ClientError as e:
                if "ExpiredToken" in str(e):
                    print("Cannot access s3 vault - you security token has expired. Renew using 'yac creds'")
                    exit(0)
                else:
                    raise e

        return object_exists

def get_vault_local_path(vault_bucket,vault_path):

    home = os.path.expanduser("~")
    vault_file_local_path = os.path.join(home, '.yac', vault_bucket, vault_path)
    vault_file_local_dir = os.path.dirname(vault_file_local_path)
    # make sure local path exists
    if not os.path.exists(vault_file_local_dir):
        os.makedirs(vault_file_local_dir)

    return vault_file_local_path