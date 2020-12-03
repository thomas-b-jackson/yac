import unittest, os, random
from yac.lib.naming import get_resource_name
from yac.lib.params import Params
from jsonschema import ValidationError


class TestCase(unittest.TestCase):

    def test_named_resource(self):

        params = {
            "service-alias": {
                "comment": "my service alias",
                "value": "jira"
            },
            "env": {
                "comment": "environment",
                "value": "dev"
            }
        }

        resource_name = get_resource_name(Params(params), "asg")

        self.assertTrue(resource_name == 'jira-asg')

    def test_unnamed_resource(self):

        params = {
            "service-alias": {
                "comment": "my service alias",
                "value": "jira"
            },
            "env": {
                "comment": "environment",
                "value": "dev"
            }
        }

        resource_name = get_resource_name(Params(params), "")

        self.assertTrue(resource_name == 'jira')

    def test_via_custom_convention(self):

        params = {
            "service-alias": {
                "comment": "my service alias",
                "value": "jira"
            },
            "env": {
                "comment": "environment",
                "value": "dev"
            },
            "naming-convention": {
                "comment": "my custom naming convention",
                "value": {
                    "param-keys": ['service-alias','env'],
                    "delimitter": "-"
                }
            }
          }
        resource_name = get_resource_name(Params(params), "elb")

        self.assertTrue(resource_name == 'jira-dev-elb')


    def test_via_custom_convention_temp(self):

        params = {
            "service-alias": {
                "comment": "my service alias",
                "value": "jira"
            },
            "env": {
                "comment": "environment",
                "value": "dev"
            },
            "naming-convention": {
                "comment": "my custom naming convention",
                "value": {
                    "param-keys": ['service-alias','env'],
                    "delimitter_fake": "-"
                }
            }
          }

        validation_errors = False

        try:
            resource_name = get_resource_name(Params(params), "elb")

        except ValidationError as e:
            validation_errors = True


        self.assertTrue(validation_errors)
