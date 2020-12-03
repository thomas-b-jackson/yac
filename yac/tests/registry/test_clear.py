
import unittest, os, requests, random
from yac.lib.registry import get_remote_value, set_remote_string_w_challenge
from yac.lib.registry import clear_entry_w_challenge
from yac.lib.registry import RegError, get_private_registry, set_private_registry, MOCK_REGISTRY_DESC
from yac.lib.registry import clear_private_registry

class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # save currently configured registry so it can be re-set at the 
        # conclusion of testing
        cls.current_registry = get_private_registry()

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

    # test that re-registering with the same challenge phrase succeeds
    def test_clear(self): 
        
        # create a random value to put into registry
        test_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        challenge_phrase = 'test'
        
        set_remote_string_w_challenge(test_key, test_value, challenge_phrase)

        test_value = "test-value-" + str(random.randint(1, 1000))

        # clear the value in registry
        clear_entry_w_challenge(test_key, challenge_phrase)

        # pull value back out
        returned_value = get_remote_value(test_key)

        # test that the clear was successful
        self.assertTrue( not returned_value ) 

    # test that deleting with/out the original challenge phrase fails
    def test_clear_fail(self): 
        
        # create a random value to put into registry
        original_value = "test-value-" + str(random.randint(1, 1000))
        test_key = "test-key-" + str(random.randint(1, 1000))

        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))
        
        set_remote_string_w_challenge(test_key, original_value, challenge_phrase)

        new_value = "test-value-" + str(random.randint(1, 1000))

        try:
            # attempt clear with a different phrase
            clear_entry_w_challenge(test_key, challenge_phrase + 'deviation')
        except RegError as e:
            # we expect to get an error
            print(e.msg)

        # pull value back out
        returned_value = get_remote_value(test_key)

        # test that the original value remains
        self.assertTrue(returned_value == original_value)
               
 