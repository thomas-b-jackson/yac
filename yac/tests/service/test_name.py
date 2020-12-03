import unittest, os, random
from yac.lib.service import is_service_name_complete, get_complete_name
from yac.lib.service import register_service, clear_service
from yac.lib.registry import get_private_registry, set_private_registry, MOCK_REGISTRY_DESC

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

        # re-set users private registry 
        set_private_registry(cls.current_registry)

    def test_service_name(self): 

        service_name = "nordstromsets/jira:35"

        self.assertTrue(is_service_name_complete(service_name))

    def test_service_incomplete_name(self): 

        service_name = "nordstromsets/jira"

        self.assertTrue(not is_service_name_complete(service_name))

    def test_get_complete_name(self): 

        incomplete_service_name = "myservice" + str(random.randint(1, 1000))

        # set up test vector
        service_path = 'yac/tests/service/vectors/simple_service.json'

        complete_service_name = "%s:%s"%(incomplete_service_name,"latest")

        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))

        # register the complete service
        register_service(complete_service_name, service_path, challenge_phrase)

        # run test
        complete_service_name_returned = get_complete_name(incomplete_service_name)

        # clean up
        clear_service(complete_service_name, challenge_phrase)

        # test that get_complete_name found the latest version of the service
        self.assertTrue(complete_service_name_returned == complete_service_name)

     