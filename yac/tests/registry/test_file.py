import unittest, os, random
from yac.lib.file import register_file, get_file_from_registry
from yac.lib.file import clear_file_from_registry
from yac.lib.file import FileError, get_file_contents
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

    def test_register_file(self):

        file_path =  "yac/tests/registry/vectors/local_file.txt"
        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))
        file_key = '%s:%s'%(file_path,str(random.randint(1, 1000)))

        register_file(file_key, file_path, challenge_phrase)

        # read file back out
        file_contents_returned = get_file_from_registry(file_key)

        # clean up - remove the test file from the registry
        clear_file_from_registry(file_key,challenge_phrase)

        file_contents_sent = get_file_contents(file_path)

        # test that the create was successful
        self.assertTrue(file_contents_sent == file_contents_returned)


    def test_no_file(self):

        # non-existent file
        file_path = "/yo/mamma/is/so"
        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))
        file_key = '%s:%s'%(file_path,str(random.randint(1, 1000)))

        file_exists_error=False
        try:
            register_file(file_key, file_path, challenge_phrase)

            # clean up - remove the test file from the registry
            clear_file_from_registry(file_key,challenge_phrase)
        except FileError:
            file_exists_error = True

        # test that the error was thrown
        self.assertTrue(file_exists_error)