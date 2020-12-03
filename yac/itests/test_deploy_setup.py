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
            "setup": "yac/tests/test_vectors/deploy/setup.py",
            "stages": [
                {
                    "name": "dev",
                    "kvps": "env:dev",
                    "test-groups": ["performance-suite","regression-suite"]
                }
            ]
        }

        deployer = Deployer(deploy_description,
                 "my-service:1.0",
                 "/any/path",
                 "https://myrepo",
                 "my-service-dev")

        deployer.run(stage_names=[], 
                       service_alias="",
                       local_servicefile_bool=True,
                       dry_run_bool=True)

        setup_value = get_variable(params,'setup-variable')
        
        self.assertTrue(setup_value = "start me up!")        
     