import unittest, os
from jsonschema import ValidationError
from yac.lib.stacks.k8s.credentials import NordstromK8sCredentialer

class TestCase(unittest.TestCase):

    def test_schema_good1(self):

        serialized_obj = {
          "type": "nordstrom-k8s",
          "name": "k8s",
          "namespace": {"yac-ref": "namespace"},
          "clusters": ["nonprod"],
          "Inputs": [
            {
              "key": "namespace",
              "title": "K8s Namespace",
              "help":  "A namespace in the nonprod cluster (aka hydrogen) you have write access to",
              "type": "string",
              "required": True
            }
          ]
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            creds = NordstromK8sCredentialer(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            # for debugging ...
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_good2(self):

        serialized_obj = {
          "type": "nordstrom-k8s",
          "name": "k8s",
          "namespace": {"yac-ref": "namespace"},
          "clusters": ["nonprod"],
          "tokens": [{"yac-ref": "builder-token-nonprod"}],
          "Inputs": [
            {
              "key": "namespace",
              "title": "K8s Namespace",
              "help":  "A namespace in the nonprod cluster (aka hydrogen) you have write access to",
              "type": "string",
              "required": True
            }
          ],
          "Secrets": {
            "builder-token-nonprod": {
              "comment": "token for our k8s 'builder' service account in the nonprod cluster",
              "source": "builder",
              "lookup": "builder_token.nonprod"
            }
          }
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            creds = NordstromK8sCredentialer(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            # for debugging ...
            print(e)

        self.assertTrue(validation_success==True)