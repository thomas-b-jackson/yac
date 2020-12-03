import unittest, os, random
from yac.lib.file import get_file_contents
from yac.lib.stack import cp_file_to_s3, sync_dir_to_s3
from yac.lib.file import FileError

def raw_input_default(msg, default):

	input = input(msg)

	if not input:
		input = default

	return input

class TestCase(unittest.TestCase):

    def test_deploy_file(self): 

		source_file = "yac/tests/test_vectors/app/deploy_for_boot.txt"
		default_s3_path = "s3://tts-sets-team/test/yac"

		destination_s3_path = input(" Input destination S3 bucket w/ path [default=%s] >> "%default_s3_path)

		if not destination_s3_path:
			destination_s3_path = default_s3_path

		destination_s3_url = '%s/%s'%(destination_s3_path,"deploy_for_boot.txt")

		# deploy the file
		success = 'n'
		try:
			cp_file_to_s3(source_file, destination_s3_url)
			success = raw_input_default("%s file present in s3? (y/n) [default=%s] >> "%(destination_s3_url,'y'), 'y')

		except FileError as e:
			print(e.msg)

		self.assertTrue(success=='y')

    def test_deploy_dir(self): 

		source_dir = "yac/tests/test_vectors/templates/sample_dir"
		default_s3_path = "s3://tts-sets-team/test/yac/sample_dir"

		destination_s3_path = input(" Input destination S3 bucket w/ path [default=%s] >> "%default_s3_path)

		if not destination_s3_path:
			destination_s3_path = default_s3_path

		# deploy the file
		success = 'n'
		try:
			sync_dir_to_s3(source_dir, destination_s3_path)
			success = raw_input_default("%s directory struct maintained in s3? (y/n) [default=%s] >> "%(destination_s3_path,'y'), 'y')

		except FileError as e:
			print(e.msg)

		self.assertTrue(success=='y')		




