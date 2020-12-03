import unittest, os, random
from yac.lib.service import register_service, get_service_by_name
from yac.lib.service import clear_service, get_all_service_names
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

    # test that clearing a service from the registry does in fact clear it
    def test_register_service_clear(self):

        service_path = 'yac/tests/service/vectors/simple_service.json'

        service_name = "myservice:" + str(random.randint(1, 1000))

        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))

        # register this service
        register_service(service_name,service_path, challenge_phrase)

        # pull service back out
        returned_service = get_service_by_name(service_name)

        # clear service
        clear_service(service_name, challenge_phrase)

        # pull service back out again
        post_clear_returned_service = get_service_by_name(service_name)

        self.assertTrue(returned_service  and not post_clear_returned_service)
