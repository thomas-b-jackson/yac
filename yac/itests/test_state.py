import unittest, os, random
from yac.lib.state import find_bucket_with_state_in_cache, set_state_cache,  clear_state_cache, save_state

class TestCase(unittest.TestCase):

    def test_state_cache_miss(self):

        # this should never return a bucket
        s3_bucket, this_s3_path = find_bucket_with_state_in_cache(s3_path="testing", service_alias="gibberish")

        self.assertTrue(not s3_bucket)

    def test_state_cache_hit(self):

        random_value = 'my new random value: %s'%str(random.randint(1, 1000))

        test_state = {
            "key": {
                "comment": "my comment",
                "value": random_value
            }
        }

        service_alias="test"
        s3_path="dev"
        
        s3_bucket_dest = save_state(s3_path=s3_path, service_alias=service_alias, state=test_state)

        # save this to bucket to cache
        set_state_cache(service_alias, s3_bucket_dest)

        # this should return a bucket
        s3_bucket_found, this_s3_path = find_bucket_with_state_in_cache(s3_path=s3_path, service_alias=service_alias)

        # clear cache
        clear_state_cache(service_alias)

        self.assertTrue(s3_bucket_dest == s3_bucket_found)