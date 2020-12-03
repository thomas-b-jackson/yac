
import time
import kubernetes.client
from kubernetes.client.rest import ApiException
from pprint import pprint

configuration = kubernetes.client.Configuration()

# decode token from service account secret as:
# echo <token value in secret file> | base64 -D
# put the decoded token 
configuration.api_key['authorization'] = '<decoded token>'
configuration.api_key_prefix['authorization'] = 'Bearer'
configuration.host = 'https://cluster-1.platform-nonprod.r53.nordstrom.net'
configuration.ssl_ca_cert = '/Users/x0ox/.kube/security/ca_nonprod.pem'

api_instance = kubernetes.client.ExtensionsV1beta1Api(kubernetes.client.ApiClient(configuration))
api_instance.read_namespaced_deployment("google-mon","sets")