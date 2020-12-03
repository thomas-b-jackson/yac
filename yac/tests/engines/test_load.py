import unittest, os, random
from yac.lib.engines import get_engine_configs,get_stack_provider,load_artifact_obj
from yac.lib.engines import get_credentials_provider, get_vault_provider

class TestCase(unittest.TestCase):

    def test_load(self):

        configs = get_engine_configs()

        self.assertTrue(configs)

    def test_k8s_load(self):

        stack,err = get_stack_provider('kubernetes', {})

        self.assertTrue(not err)

    def test_aws_load(self):

        stack,err = get_stack_provider('aws-cloudformation', {})

        self.assertTrue(not err)

    def test_ami_load(self):

        ami,err = load_artifact_obj('ami', {})

        print(err)
        self.assertTrue(not err)

    def test_k8s_creds_load(self):

        creds,err = get_credentials_provider('nordstrom-k8s', {})
        self.assertTrue(not err)

    def test_s3_vault_load(self):

        vault,err = get_vault_provider('s3', {})
        self.assertTrue(not err)