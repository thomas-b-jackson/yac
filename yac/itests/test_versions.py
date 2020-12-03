import unittest, os, requests, time
from yac.lib.version import get_latest_version

class TestCase(unittest.TestCase):

    def test_versions(self): 
        
        latest_version = get_latest_version('jira','nordstromsets')

        # test that the create was successful
        self.assertTrue(latest_version == '6.3.10')