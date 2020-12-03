import unittest, os, random
from yac.lib.service import get_service
from yac.lib.file import dump_dictionary

class TestCase(unittest.TestCase):

    def test_load_from_file(self):

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

        # pull service back out
        service,err = get_service(service_path)

        self.assertTrue(service.description.name == service_name)
