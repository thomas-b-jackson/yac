import unittest, os, time, random, datetime
from yac.lib.cache import get_cache_value, set_cache_value_ms
from yac.lib.cache import set_cache_value_dt

class TestCase(unittest.TestCase):

    def test_set_no_expiration(self):

        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        set_cache_value_ms(test_key, test_value)

        # pull value back out
        returned_value = get_cache_value(test_key)

        # test that value comes back
        self.assertTrue( test_value ==  returned_value)

    def test_set_expired_ms(self):

        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        # set expiration to current time minus a second
        expiration_ms = int(time.time() * 1000) - 1000

        set_cache_value_ms(test_key, test_value, expiration_ms)

        # pull value back out
        returned_value = get_cache_value(test_key)

        # test that a null value comes back
        self.assertTrue( not returned_value )

    def test_set_expired_dt(self):

        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        # set expiration to current time minus a day
        expiration_dt = datetime.datetime.now() - datetime.timedelta(days=1)

        set_cache_value_dt(test_key, test_value, expiration_dt)

        # pull value back out
        returned_value = get_cache_value(test_key)

        # test that a null value comes back
        self.assertTrue( not returned_value )

    def test_set_unexpired_ms(self):

        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        # set expiration to current time plus a few seconds
        expiration_ms = int(time.time() * 1000) + 5000
        set_cache_value_ms(test_key, test_value, expiration_ms)

        # pull value back out
        returned_value = get_cache_value(test_key)

        # test that value comes back
        self.assertTrue( test_value ==  returned_value)

    def test_set_unexpired_dt(self):

        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        # set expiration to current time plus a few seconds
        expiration_dt = datetime.datetime.now() + datetime.timedelta(seconds=5)
        set_cache_value_dt(test_key, test_value, expiration_dt)

        # pull value back out
        returned_value = get_cache_value(test_key)

        # test that value comes back
        self.assertTrue( test_value ==  returned_value)