import unittest, os, random
from yac.lib.file import get_file_reg_key, clear_file_from_registry
from yac.lib.file_converter import find_and_convert_locals
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

    def test_file_converter(self): 

        file_path1 = "yac/tests/registry/vectors/local_file1.txt"
        file_path2 = "yac/tests/registry/vectors/local_file2.txt"
        test_dict = {
            "myparam": {
                "comment": "testing",
                "value": file_path1
            },
            "my-list": [1,2,3],
            "my-dict": {
                "my-sub-dict": {
                    "comment": "testing",
                    "value": file_path2                    
                }
            }
        }

        service_key = "myservice:" + str(random.randint(1, 1000))
        challenge_phrase = 'test-challenge' + str(random.randint(1, 1000))
        
        file_key1 = '%s/%s'%(service_key,file_path1)
        file_key2 = '%s/%s'%(service_key,file_path2)

        # run test
        updated_dict = find_and_convert_locals(test_dict, service_key, ".", challenge_phrase)
        
        # test that the file has been uploaded and that the updated dictionary has
        # registry urls associated with the files
        reg_key1 = get_file_reg_key(file_key1)
        reg_key2 = get_file_reg_key(file_key2)

        # clean up - remove file
        clear_file_from_registry(file_key1,challenge_phrase)
        clear_file_from_registry(file_key2,challenge_phrase)

        conversion_check = (updated_dict['myparam']['value'] == reg_key1 and
                            updated_dict['my-dict']['my-sub-dict']['value'] == reg_key2)

        self.assertTrue(conversion_check)                                   