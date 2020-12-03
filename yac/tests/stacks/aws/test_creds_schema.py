import unittest, os
from jsonschema import ValidationError
from yac.lib.stacks.aws.credentials import NordstromAWSCredentialer

class TestCase(unittest.TestCase):

    def test_schema_good(self):

        serialized_obj = {
          "type": "nordstrom-aws",
          "name": "aws",
          "accounts": [
            {
              "profile": "someaccount",
              "name": {"yac-ref": "aws-account-name"},
              "default": True
            }
          ],
          "Inputs": [
            {
              "key": "aws-account-name",
              "title": "AWS Account Name",
              "help":  "The name of the AWS account to build to (e.g. NORD-NonProd_DOTS-DevUsers-Team)",
              "type": "string",
              "required": True
            }
          ]
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            creds = NordstromAWSCredentialer(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==True)


    def test_schema_bad(self):

        serialized_obj = {
          "type": "nordstrom-aws",
          "accounts": [
            {
              "profile": "someaccount",
              "name": {"yac-ref": "aws-account-name"},
              "default": True
            }
          ],
          "Inputs": [
            {
              "key": "aws-account-name",
              "title": "AWS Account Name",
              "help":  "The name of the AWS account to build to (e.g. NORD-NonProd_DOTS-DevUsers-Team)",
              "type": "string",
              "required": True
            }
          ]
        }

        # test that schema validation errors are raised
        validation_success = True
        try:
            creds = NordstromAWSCredentialer(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed. but succeeded as well")
            # print(e)

        self.assertTrue(validation_success==False)

    def test_required_Properties_bad(self):

        serialized_obj = {
          "type": "nordstrom-aws",
          "Foo": "Bar",
          "accounts": [
            {
              "profile": "someaccount",
              "name": {"yac-ref": "aws-account-name"},
              "default": True
            }
          ],
          "Inputs": [
            {
              "key": "aws-account-name",
              "title": "AWS Account Name",
              "help":  "The name of the AWS account to build to (e.g. NORD-NonProd_DOTS-DevUsers-Team)",
              "type": "string",
              "required": True
            }
          ]
        }

        # test that no schema validation errors are raised
        validation_success = True
        try:
            creds = NordstromAWSCredentialer(serialized_obj)
        except ValidationError as e:
            validation_success = False
            print("validation failed")
            print(e)

        self.assertTrue(validation_success==False)