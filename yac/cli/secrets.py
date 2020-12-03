import os, sys, json, yaml, argparse
from subprocess import call

from yac.lib.service import get_service
from yac.lib.file import get_file_contents
from yac.lib.secrets import Secrets
from yac.lib.params import Params

def main():

    parser = argparse.ArgumentParser('View and edit the content of an s3 vault')

    # required args
    parser.add_argument('servicefile', help='location of the Servicefile (registry key or local path)')
    parser.add_argument('vault', help='name of the s3 vault')
    parser.add_argument('--edit', help='edit the vault',
                                  action='store_true')
    args = parser.parse_args()

    service, err = get_service(args.servicefile)

    if not err:
        vault = service.vaults.get_vault(args.vault)

        if vault:

            # load secrets
            params = service.get_all_params()

            errors = service.secrets.get_errors()

            if errors:
                print("secrets file has the following load errors")
                print("errors: \n%s"%json.dumps(errors,indent=2))
            else:
                print(("'%s' vault and the secrets that "%args.vault +
                       "reference the vault are AOK!"))

            if vault.get_type() == 's3' and not err and args.edit:

                err = True

                while err or service.secrets.errors:

                    # give user opportunity to view/edit the secrets in the vault
                    updated_secrets, err = edit_secrets(vault)

                    if not err:

                        # update the vault with the updated secrets
                        vault.update(updated_secrets)

                        # clear any existing secret errors
                        service.secrets.clear_errors()

                        # reload the updated secrets to make sure no errors occur
                        service.secrets.load(params,
                                             service.vaults)

                        if service.secrets.get_errors():
                            print("updated secrets file resulted in the following load errors")
                            print("errors: \n%s"%service.secrets.get_errors())
                            input("Hit <enter> to try again ...")

                    else:
                        print("secrets file does not contain well formatted json")
                        print("errors: \n%s"%err)
                        input("Hit <enter> to try again ...")

                print ("'%s' vault and the secrets that "%args.vault +
                       "reference the vault are AOK!")

            elif vault.get_type() == 's3' and not vault.initialized:
                print("vault specified exists but is not currently available. are your aws credentials fresh?")

        else:
            all_vaults = service.vaults.get_vaults()

            print("vault specified does not exist, available vaults include:")

            for vault_key in list(all_vaults.keys()):
                print("* " + vault_key)

    else:
        print("servicefile could not be loaded from %s"%args.servicefile)
        print("error: %s"%err)

def view_secrets(vault):

    if vault.vault_path:

        # load the file contents into a dictionary
        file_contents = get_file_contents(vault.vault_path)

        print(file_contents)


def edit_secrets(vault):

    err = ""
    new_secrets = {}

    if vault.vault_path:

        # open an editor session so user can edit the file
        if os.environ.get('EDITOR'):
            EDITOR = os.environ.get('EDITOR')
        else:
            EDITOR = 'nano'

        call([EDITOR, vault.vault_path])

        # load the file contents back into a dictionary
        file_contents = get_file_contents(vault.vault_path)

        # parse the secrets to make sure the string is well formatted
        if file_contents:

            if vault.get_format() == "json":
                try:
                    new_secrets = json.loads(file_contents)
                except ValueError as e:
                    err = str(e)
            elif vault.get_format() == "yaml":
                try:
                    new_secrets = yaml.load(file_contents)
                except yaml.scanner.ScannerError as e:
                    err = str(e)

        return file_contents, err

def save_secrets(vault):

    vault.deserialize(new_secrets)
