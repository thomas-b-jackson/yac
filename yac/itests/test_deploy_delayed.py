import unittest, os, random, datetime
from yac.lib.deploy import Deployer

class TestCase(unittest.TestCase):

    def test_deploy_delayed(self):

        now = datetime.datetime.today()
        now_hr = now.hour
        now_min = now.minute

        # delay start for 16 minutes
        start_time = "%s:%s"%(now_hr, str(now_min+16))

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
                    "start-time": start_time
                }
            ]
        }

        params = {}
        set_variable(params,"stack-name", "test-stack-dev")

        deployer = Deployer(deploy_description,params)

        deployer.deploy(dry_run=True)

        self.assertTrue(True)
