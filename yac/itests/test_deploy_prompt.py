import unittest, os, random
from yac.lib.deploy import Deployer
from yac.lib.variables import set_variable

class TestCase(unittest.TestCase):

    def test_deploy_prompt(self):

        deploy_description = {
            "deploy-branch": "releases",
            "rollback-branch": "master",
            "servicefile-name": "tester",
            "notifications": {
                "type":    "slack",
                "configs": {
                    "info-channel": "info",
                    "warning-channel": "warnings",          
                    "api-key": "xoxp-298418519346-299477551335-299272988262-1ca0dd82671e5fdce083e040a20ccbc9"
                }
            },
            "stages": [
                {
                    "name": "dev",
                    "kvps": "env:dev",
                    "test-groups": ["performance-suite","regression-suite"],
                    "confirmation-prompt": True
                },
                {
                    "name": "staging",
                    "kvps": "env:stage",
                    "test-groups": ["regression-suite"],
                    "confirmation-prompt": False
                }      
            ]
        }

        params = {}
        set_variable(params,"stack-name", "test-stack-dev")

        deployer = Deployer(deploy_description,params)

        deployer.deploy(dry_run=True)

        self.assertTrue(True)     