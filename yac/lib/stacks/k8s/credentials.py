#!/usr/bin/env python

import json, requests, os, subprocess, getpass, sys, socket, shutil, stat
import datetime as dt
import kubernetes.config
from yac.lib.logger import get_yac_logger
from yac.lib.search import search
from yac.lib.file import get_file_contents
from yac.lib.params import Params
from yac.lib.template import apply_stemplate
from yac.lib.intrinsic import apply_intrinsics
from yac.lib.inputs import Inputs
from yac.lib.paths import get_root_path
from yac.lib.secrets import Secrets
from yac.lib.schema import validate

#PROD1_CERT_URL="http://certificates.platform.r53.nordstrom.net/steel/kubernetes/ca.pem"
PROD1_CERT_URL="http://certificates.us-west-2.platform.r53.nordstrom.net/steel/kubernetes/ca.pem"
#PROD2_CERT_URL="http://certificates.platform.r53.nordstrom.net/barcelona/kubernetes/ca.pem"
PROD2_CERT_URL="http://certificates.us-west-2.platform.r53.nordstrom.net/barcelona/kubernetes/ca.pem"

NONPROD_PUBLIC_API="https://api.cluster-1.nonprod.us-west-2.aws.platform.vip.nordstrom.com"
NONPROD_PRIVATE_API="https://cluster-1.platform-nonprod.r53.nordstrom.net"

NONPROD_PUBLIC_CERT_URL="http://certificates.us-west-2.platform-nonprod.r53.nordstrom.net/hydrogen/kubernetes/ca.pem"
NONPROD_PRIVATE_CERT_URL="http://certificates.us-west-2.platform-nonprod.r53.nordstrom.net/hydrogen/kubernetes/ca.pem"

class NordstromK8sCredentialer():

    def __init__(self,
                 credentials_descriptor):

        validate(credentials_descriptor, "yac/schema/stacks/k8s/credentialer.json")

        self.namespace = search("namespace",
                               credentials_descriptor,"")

        self.clusters = search("clusters",
                               credentials_descriptor,
                               ["nonprod","prod"])

        # if tokens are input there should be one per cluster
        self.tokens = search("tokens",
                               credentials_descriptor,
                               [])

        self.secrets = Secrets(search('"Secrets"',
                               credentials_descriptor,{}))

        # initialize the inputs (for driving user prompts)
        self.inputs = Inputs(search("Inputs",
                                    credentials_descriptor,{}))

        # for integration testing it is useful to write files to a
        # root director other than user's home
        self.rootdir = search("rootdir",
                              credentials_descriptor,"")

    def create(self,
               params,
               vaults,
               overwrite_bool):

        self.params = params

        # process creds-specific inputs and load results into params
        self.inputs.load(self.params)

        # load any creds-specific secrets into params
        self.secrets.load(self.params,vaults)

        # determine if credentialer is being instantiated on a developer
        # desktop
        self.is_desktop = self.running_on_desktop()

        err = ""
        if overwrite_bool or not self.created_today(".kube/config"):

            # make sure certs are in place
            err = self.install_root_ca_certs()

            # install ~/.kubeloginrc.yaml file
            # note: file is only needed when running on a desktop
            if not err and self.is_desktop:
                self.install_kube_login()

            # create ~/.kube/config file
            if not err:
                self.install_kube_config(params)

            if not err and not self.tokens:
                # explain how to create tokens for the target clusters
                self.token_help()

        else:
            print("k8s ~/.kube/config file has fresh tokens so won't be updated ...")

        return err

    def token_help(self):

        for cluster in self.clusters:

            self.show_kubelogin_help(cluster)

        input("press <enter> when you've completed the kubelogin for all clusters ... >> ")

    def install_root_ca_certs(self):

        # install each cert
        err = self.download_cert(PROD1_CERT_URL,".kube/certs/prod1.pem")

        # stop after the first error
        if not err:
            err = self.download_cert(PROD2_CERT_URL,".kube/certs/prod2.pem")

        if not err:

            if self.is_desktop:
                err = self.download_cert(NONPROD_PRIVATE_CERT_URL,".kube/certs/nonprod.pem")
            else:
                err = self.download_cert(NONPROD_PUBLIC_CERT_URL,".kube/certs/nonprod.pem")

        return err


    def download_cert(self, url, home_rel_path):

        err = ""
        r = requests.get(url, allow_redirects=True)

        if r.status_code == 200:
            self.write_home_file(r.content.decode("utf-8"),home_rel_path)
        else:
            err = "could not download root CA cert from %s"%url

        return err

    def install_kube_config(self, params):

        # use .kubeconfig.yaml as a template
        with open(os.path.join(get_root_path(),
            "lib/stacks/k8s/configs/.kubeconfig.yaml"), 'r') as config_file:
            file_contents = config_file.read()

        # render mustaches in the file ...

        # first worry about how to render the 'token' token in the
        # file

        # use placeholder values (o.w. apply_stemplate will raise TemplateError).
        # the user will need to use kubelogin to overwrite
        stock_tokens = ["via kubelogin", "via kubelogin", "via kubelogin"]

        if not self.tokens:
            # no tokens are provided via servicefile. this is a typical pattern
            # for servicefiles that are meant to be run from a developer desktop.
            tokens = stock_tokens

        else:
            tmp_tokens = stock_tokens

            # make sure there is one token per cluster
            tmp_tokens[0:len(self.tokens)] = self.tokens

            # tokens were specified in the servicefile
            # these will typically include secrets that are referenced
            # via a yac-ref intrinstric, so render intrinsics in the tokens
            tokens = apply_intrinsics(tmp_tokens, params)

        # build the params for each variable in the file
        local_params = Params({})

        # set variables for each of the cluster tokens
        cluster_keys = ["nonprod-token","prod1-token","prod2-token"]

        for i,token in enumerate(tokens):
            local_params.set(cluster_keys[i],token)

        # the namespace params supports intrinsics (so that it can be set via an input)
        namespace = apply_intrinsics(self.namespace, params)

        # set namespace variable for template rendering
        local_params.set("namespace", namespace)

        if self.is_desktop:
            # use the private api to avoid the limitations of the public
            # api endpoint, per:
            #  * https://gitlab.nordstrom.com/k8s/platform-bootstrap/wikis/Onboard-to-AWS-Kubernetes-Clusters
            local_params.set("nonprod-api-url",NONPROD_PRIVATE_API)
        else:
            # pipelines must use the public to avoid v2 account peering
            # contraints
            local_params.set("nonprod-api-url",NONPROD_PUBLIC_API)

        # do the actual mustache rendering
        rendered_file_contents = apply_stemplate(file_contents,local_params)

        # take backup of any existing .kube/config files
        self.backup_existing(".kube/config")

        # write file
        self.write_home_file(rendered_file_contents,".kube/config")

    def install_kube_login(self):

        # get the contents of the .kube/config file
        file_contents = get_file_contents('yac/lib/stacks/k8s/configs/.kubeloginrc.yaml')

        # write file
        self.write_home_file(file_contents,".kubeloginrc.yaml")

        # copy the kubelogin app under the user's home dir
        kubelogin_dest = self.get_kubelogin_path()

        if os.path.exists(kubelogin_dest):
            # remove existing installatiaon of kubelogin
            os.remove(kubelogin_dest)

        print("installing: %s"%kubelogin_dest)

        shutil.copyfile('yac/lib/stacks/k8s/configs/kubelogin',
                        kubelogin_dest)
        os.chmod(kubelogin_dest, stat.S_IREAD | stat.S_IEXEC )

    def backup_existing(self,home_rel_path):

        full_home_path = get_home_path(home_rel_path)

        if os.path.exists(full_home_path):
            # rename existing file
            timestamp = "{:%Y-%m-%d.%H.%M.%S}".format(dt.datetime.now())
            backup_filename = "%s.%s"%(full_home_path,timestamp)
            print("backing up existing ~/.kube/config file to: %s"%backup_filename)
            os.rename(full_home_path,
                      backup_filename)

    def write_home_file(self, content, home_rel_path):

        full_home_path = get_home_path(home_rel_path)

        if not os.path.exists(os.path.dirname(full_home_path)):
            os.makedirs(os.path.dirname(full_home_path))

        print("writing: %s"%(full_home_path))

        open(full_home_path, 'w').write(content)

    def show_kubelogin_help(self, cluster):

        # from the kubelogin command
        kubelogin_path = self.get_kubelogin_path()
        kubelogin_cmd = "%s login %s"%(kubelogin_path,cluster)

        print("run the following command in a separate terminal to generate credentials for the %s cluster:"%cluster)

        print("$ {0}".format( kubelogin_cmd ))

    def created_today(self, home_rel_path):

        # returns true if the the file at home_rel_path was created today
        created_today=False

        full_home_path = get_home_path(home_rel_path)

        if os.path.exists(full_home_path):

            today = dt.datetime.now().date()

            filetime = dt.datetime.fromtimestamp(os.path.getctime(full_home_path))

            if filetime.date() == today:
                created_today = True

        return created_today

    def running_on_desktop(self):
        # returns true if these credentials are being created on a developer desktop
        #
        # the distinction is important for this k8s credentialer as it determines which
        # k8s api endpoint to use. the private endpoint is the most fully featured (esp for
        # kubectl commands) but is only accessible from clients joined to the nordstrom domain.
        # the public endpoint works for most use cases AND is availble from build servers
        # running in most environments (k8s clusters, aws v2 accounts, etc).
        return self.params.get('desktop')

    def get_current_context(self):

        context_name = ""

        full_home_path = get_home_path(".kube/config", self.rootdir)

        if os.path.exists(full_home_path):

            kubernetes.config.load_kube_config()

            contexts, active_context = kubernetes.config.list_kube_config_contexts()

            if ('name' in active_context ):
                context_name = active_context['name']

        return context_name

    def get_kubelogin_path(self):

        return  get_home_path(".kube/kubelogin")

def get_home_path(home_rel_path, rootdir=""):

    if not rootdir:
        full_home_path = os.path.join(os.path.expanduser("~"),home_rel_path)
    else:
        full_home_path = os.path.join(rootdir,home_rel_path)

    return full_home_path

def load_context(context):

    err = ""
    full_home_path = get_home_path(".kube/config")

    if os.path.exists(full_home_path):

        if context:
            kubernetes.config.load_kube_config(context=context)
        else:
            kubernetes.config.load_kube_config()
    else:
        err = "~.kube/config does not exist. can create using 'yac creds'..."

    return err

def get_current_namespace():

    namespace=""
    err = ""
    full_home_path = get_home_path(".kube/config")

    if os.path.exists(full_home_path):

        # get the namespace from the active context
        contexts, active_context = kubernetes.config.list_kube_config_contexts()
        if ('context' in active_context and
            'namespace' in active_context['context']):
            namespace = active_context['context']['namespace']
    else:
        err = "~.kube/config does not exist so can not determine current namespace. can create using 'yac creds'..."

    return namespace, err
