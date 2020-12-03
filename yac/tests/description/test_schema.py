import unittest, os
from jsonschema import ValidationError
from yac.lib.service import Description

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
            "name": "nordstromdot/artifactory-fe",
            "default-alias": "artifactory",
            "summary": "Front End for Artifactory",
            "details":  ["* Artifactory HA in Kubernetes",
                         "* Single primary, multiple members nodes",
                         "* Multi-cluster active/active architecture"],
            "maintainer" : {
              "name":     "DevOps Tools",
              "email":    "tech_dot_support@nordstrom.com"
            },
            "tags": ["artifacts", "k8s", "binaries", "respository"]
          }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            description = Description(serialized_obj,alias="")
        except ValidationError as e:
            validation_success = False
            print(e)

        self.assertTrue(validation_success==True)

    def test_schema_bad(self):

        serialized_obj = {
            "names": "nordstromdot/artifactory-fe",
            "default-alias": "artifactory",
            "summary": "Front End for Artifactory",
            "details":  ["* Artifactory HA in Kubernetes",
                         "* Single primary, multiple members nodes",
                         "* Multi-cluster active/active architecture"],
            "maintainer" : {
              "name":     "DevOps Tools",
              "email":    "tech_dot_support@nordstrom.com"
            },
            "tags": ["artifacts", "k8s", "binaries", "respository"]
          }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            description = Description(serialized_obj,alias="")
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)

    def test_schema_missing_name(self):
        # the name attribute is required

        serialized_obj = {
            "default-alias": "artifactory",
            "summary": "Front End for Artifactory",
            "details":  ["* Artifactory HA in Kubernetes",
                         "* Single primary, multiple members nodes",
                         "* Multi-cluster active/active architecture"],
            "maintainer" : {
              "name":     "DevOps Tools",
              "email":    "tech_dot_support@nordstrom.com"
            },
            "tags": ["artifacts", "k8s", "binaries", "respository"]
          }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            description = Description(serialized_obj,alias="")
        except ValidationError as e:
            validation_success = False

        self.assertTrue(validation_success==False)