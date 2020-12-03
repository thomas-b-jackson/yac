import unittest, os, random
from yac.lib.service import register_service, get_service_by_name, clear_service
from yac.lib.service import get_all_service_names
from yac.lib.file import file_in_registry, dump_dictionary
from yac.lib.registry import RegError, get_private_registry, set_private_registry, MOCK_REGISTRY_DESC

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

    def test_register_service(self):

        servicefile_path = os.path.join("/tmp",str(random.randint(1, 1000)))
        service_name = "myservice:" + str(random.randint(1, 1000))

        service_descriptor = {
            "Description": {"name": service_name,
                            "default-alias": "test"},
            "Stack": {
                "type": "aws-cloudformation",
                "Resources": {
                    "task-definition": "whatevs"
                }
            }
        }

        service_path = dump_dictionary(service_descriptor,
                                       servicefile_path,
                                       "servicefile.json")

        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))

        # register this service
        updated_dict = register_service(service_name, service_path, challenge_phrase)

        # pull service back out of registry
        returned_service = get_service_by_name(service_name)

        assertion_check=False

        if returned_service:

            template = returned_service.get_stack().serialize()

            assertion_check = ('Resources' in template and
                               'task-definition' in template['Resources'])

        self.assertTrue(assertion_check)

    def test_list_service(self):

        servicefile_path = os.path.join("/tmp",str(random.randint(1, 1000)))
        service_name = "myservice:" + str(random.randint(1, 1000))

        service_descriptor = {
            "Description": {"name": service_name,
                            "default-alias": "test"},
            "Stack": {
                "type": "aws-cloudformation",
                "Resources": {
                    "task-definition": "whatevs"
                }
            }
        }

        service_path = dump_dictionary(service_descriptor,
                                       servicefile_path,
                                       "servicefile.json")

        service_name1 = "myservice:" + str(random.randint(1, 1000))
        service_name2 = "myservice:" + str(random.randint(1, 1000))

        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))

        # register this service
        register_service(service_name1,service_path, challenge_phrase)
        register_service(service_name2,service_path, challenge_phrase)

        # get all service names
        all_keys = get_all_service_names()

        # verify that all the services input got returned
        keys_registered=[service_name1,service_name2]
        length_check = (len(set(keys_registered) & set(all_keys)) == len(keys_registered))

        self.assertTrue( length_check )
