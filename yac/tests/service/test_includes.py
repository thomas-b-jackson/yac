import unittest, os, random
from yac.lib.service import get_service
from yac.lib.search import search

class TestCase(unittest.TestCase):

    def test_included_resources(self):

        service_path = 'yac/tests/service/vectors/service_with_subs.json'

        # pull service back out
        service,err = get_service(service_path)

        # test that naming is per the parent service (i.e. not named per the includes)
        self.assertTrue(service.description.name == 'nordstrom/jira')

        stack = service.get_stack()

        stack_template = stack.serialize()

        resource_keys = list(stack_template['Resources'].keys())

        # test that all stack resources got pulled in
        self.assertTrue('task-definition-1' in resource_keys)
        self.assertTrue('task-definition-2' in resource_keys)
        self.assertTrue('task-definition-3' in resource_keys)
