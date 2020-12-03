import unittest, os, shutil
from yac.lib.logger import get_stack_logger, get_deploy_logger
from yac.lib.logger import get_test_logger


class TestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.test_path = "./yac/tests/tmp"

        # remove any existing test directories
        if os.path.exists(cls.test_path):
            shutil.rmtree(cls.test_path)

    @classmethod
    def tearDownClass(cls): 

        # remove the test directories
        shutil.rmtree(cls.test_path)

    def test_stack_logger(self): 

        logs_path = os.path.join(TestCase.test_path,
                                 "stack", 
                                 "my_stack_logs.out")

        logger2 = get_stack_logger(logs_path,"DEBUG")

        logger2.info("info message from logger 2")
        logger2.debug("debug message from logger 2")
        logger2.warning("warning message from logger 2")        

        log_data = ""
        with open(logs_path, 'r') as myfile:
            log_data=myfile.read()

        self.assertTrue("info" in log_data and 
                        "debug" in log_data and 
                        "warning" in log_data)
      
    def test_deploy_logger(self): 

        logs_path = os.path.join(TestCase.test_path,
                                 "deploy", 
                                 "my_stack_logs.out")

        logger1 = get_deploy_logger(logs_path,"INFO")

        logger1.info("info message from logger 1")
        logger1.debug("debug message from logger 1")
        logger1.warning("warning message from logger 1")     

        log_data = ""
        with open(logs_path, 'r') as myfile:
            log_data=myfile.read()

        self.assertTrue("info" in log_data and 
                        "debug" not in log_data and 
                        "warning" in log_data)

    def test_test_logger(self): 

        logs_path = os.path.join(TestCase.test_path,
                                 "stack", 
                                 "my_test_logs.out")

        logger1 = get_test_logger(logs_path,"INFO")

        logger1.info("info message from logger 1")
        logger1.debug("debug message from logger 1")
        logger1.warning("warning message from logger 1")     

        log_data = ""
        with open(logs_path, 'r') as myfile:
            log_data=myfile.read()

        self.assertTrue("info" in log_data and 
                        "debug" not in log_data and 
                        "warning" in log_data)         