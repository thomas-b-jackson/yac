import unittest, os, random, json
from yac.lib.state import prompt_for_bucket, find_bucket_in_cache, clear_state_cache

class TestCase(unittest.TestCase):

    def test_state_prompt(self):

        service_alias="gibberish"

        s3_bucket_input = prompt_for_bucket(service_alias)

        # bucket found should now be in cache
        s3_bucket_cached = find_bucket_in_cache(service_alias)

        # clear cache
        clear_state_cache(service_alias)

        self.assertTrue(s3_bucket_input == s3_bucket_cached)
