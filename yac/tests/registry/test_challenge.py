import unittest, os, requests, random
from yac.lib.registry import get_remote_value, set_remote_string_w_challenge, clear_entry_w_challenge
from yac.lib.registry import RegError, get_private_registry, set_private_registry, MOCK_REGISTRY_DESC
from yac.lib.registry import clear_private_registry

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # save currently configured registry so it can be re-set at the
        # conclusion of testing
        cls.current_registry = get_private_registry()

        print("private registry is currently: %s"%cls.current_registry)

        # set private registry to a mock registry
        set_private_registry(MOCK_REGISTRY_DESC)

    @classmethod
    def tearDownClass(cls):

        if cls.current_registry:
            # re-set users private registry
            set_private_registry(cls.current_registry)
        else:
            # re-set to public registry
            clear_private_registry()

    def test_register(self):

        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        # create a key/value pair in registry with a challenge phrase
        challenge_phrase = 'test'

        set_remote_string_w_challenge(test_key, test_value, challenge_phrase)

        # pull value back out
        returned_value = get_remote_value(test_key)

        # clean up test key
        clear_entry_w_challenge(test_key, challenge_phrase)

        # test that the create was successful
        self.assertTrue(test_value == returned_value)

    # test that re-registering with the same challenge phrase succeeds
    def test_re_register(self):

        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        challenge_phrase = 'test'

        set_remote_string_w_challenge(test_key, test_value, challenge_phrase)

        test_value = "test-value-" + str(random.randint(1, 1000))

        # re-create a key/value pair in registry
        set_remote_string_w_challenge(test_key, test_value, challenge_phrase)

        # pull value back out
        returned_value = get_remote_value(test_key)

        # clean up test key
        clear_entry_w_challenge(test_key, challenge_phrase)

        # test that the create was successful
        self.assertTrue(test_value == returned_value)

    # test that re-registering with/out the original challenge phrase fails
    def test_re_register_fail(self):

        # create a random value to put into registry
        original_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))

        set_remote_string_w_challenge(test_key, original_value, challenge_phrase)

        new_value = "test-value-" + str(random.randint(1, 1000))

        try:
            # attempt re-registry with a different phrase
            set_remote_string_w_challenge(test_key, new_value, challenge_phrase + 'deviation')
        except RegError as e:
            # we expect to get an error due to the challenge phrase mismatch
            print(e.msg)

        # pull value back out
        returned_value = get_remote_value(test_key)

        # clean up test key
        clear_entry_w_challenge(test_key, challenge_phrase)

        # test that the original value remains
        self.assertTrue(returned_value == original_value)
