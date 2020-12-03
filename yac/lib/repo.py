import os, subprocess, shutil

def get_local_repo_path():

    home = os.path.expanduser("~")

    dockerfile_path = ""

    build_path = os.path.join(home,'.yac','repos')

    return build_path


def get_repo_name(repo_url):

    repo_name = ""

    repo_parts = repo_url.split("/")

    repo_name_git = repo_parts[len(repo_parts)-1]

    repo_name_git_parts = repo_name_git.split('.')

    if len(repo_name_git_parts)==2:

        repo_name = repo_name_git_parts[0]

    return repo_name

def clone_repo(repo_url, branch):

    repo_path = ""

    if repo_url:
        repo_path = get_local_repo_path()

        repo_name = get_repo_name(repo_url)

        repo_full_path = os.path.join(repo_path,repo_name)

        print(repo_full_path)

        # remove the repo if it already exists
        if os.path.exists(repo_full_path):
            shutil.rmtree(repo_full_path)

        clone_command = "git clone -b %s %s %s"%(branch, repo_url, repo_full_path)

        clone_command_array = clone_command.split(" ")

        # use subprocess to execute the clone
        subprocess.check_output(clone_command_array)

    # return the path to the repo
    return repo_path