import unittest
from yac.lib.params import Params

class TestCase(unittest.TestCase):

    def test_kvp_params(self):

        kvps = "joe:blue,jan:green"

        params = Params({})
        params.load_kvps(kvps)

        self.assertTrue( params.get("jan") == 'green' )
        self.assertTrue( params.get("joe") == 'blue' )

    # include a comment
    def test_kvp_param_comment(self):

        kvps = "ami:ami-324:ami for ec2 hosts,vpc-id:vpc-325552:id of nonprod vpc"

        params = Params({})
        params.load_kvps(kvps)

        self.assertTrue(params.get("ami") == 'ami-324')
        self.assertTrue(params.get("vpc-id") == 'vpc-325552')