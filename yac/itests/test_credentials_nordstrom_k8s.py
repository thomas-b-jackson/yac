import unittest, os, random
from yac.lib.credentials import NordstromK8sCredentialer

class TestCase(unittest.TestCase):


    @classmethod
    def setUpClass(cls):

        cls.rootdir = "/tmp/creds_test"

        # create the test dir
        if cls.rootdir and not os.path.exists(cls.rootdir):
            os.makedirs(cls.rootdir)


    def test_credentials(self):

        credentials_config = {
            "namespace": "sets",          
            "rootdir": TestCase.rootdir
        }

        credentials = NordstromK8sCredentialer(credentials_config)

        err = credentials.create()

        print(err)

        self.assertTrue(not err)