import unittest, os, random
from yac.lib.credentials import NordstromAWSCredentials

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # make sure any existing credentials are removed
        cls.credentials_file_path = os.path.join(os.path.expanduser("~"),
                                             ".aws",
                                             "credentials")

        if os.path.exists(cls.credentials_file_path):
            os.remove(cls.credentials_file_path)

    @classmethod
    def tearDownClass(cls): 

        if os.path.exists(cls.credentials_file_path):
            os.remove(cls.credentials_file_path)

    def test_credentials_with_urls(self):

        credentials_config = {
            "token-endpoint-url": "https://pbcld-awsToken.nordstrom.net/authentication/awsToken",
            "role-endpoint-url": "https://pbcld-awsToken.nordstrom.net/authentication/roleArns",          
            "account": "NORD-NonProd_DOTS-DevUsers-Team"
        }

        credentials = NordstromAWSCredentials(credentials_config)

        credentials.create()

        credentials_contents = ""
        if os.path.exists(TestCase.credentials_file_path):
            with open(TestCase.credentials_file_path, 'r') as myfile:
                credentials_contents=myfile.read()

        self.assertTrue("region" in credentials_contents)

    def test_credentials_without_urls(self):

        credentials_config = {
            "account": "NORD-NonProd_DOTS-DevUsers-Team"
        }

        credentials = NordstromAWSCredentials(credentials_config)

        credentials.create()

        credentials_contents = ""
        if os.path.exists(TestCase.credentials_file_path):
            with open(TestCase.credentials_file_path, 'r') as myfile:
                credentials_contents=myfile.read()

        self.assertTrue("region" in credentials_contents)