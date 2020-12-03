import unittest, os
from yac.lib.test import TestResults

class TestCase(unittest.TestCase):

    def test_passing_results(self): 
    
        test_results = TestResults()

        # register successful results
        test_results.passing_test("test1")
        test_results.passing_test("test2")

        exit_code = test_results.process()

        passing_tests = test_results.get_passing_tests()

        # test for a success exit code
        self.assertTrue(len(passing_tests)==2 and exit_code == 0)

    def test_failing_results(self): 
    
        test_results = TestResults()

        # register successful results
        test_results.passing_test("test1")
        test_results.passing_test("test2")

        # register failing results
        test_results.failing_test("test3", "test 3 failure msg")
        test_results.failing_test("test4", "test 4 failure msg")

        exit_code = test_results.process()

        passing_tests = test_results.get_passing_tests()
        failing_tests = test_results.get_failing_tests()

        # test for a failure exit code
        self.assertTrue(len(passing_tests)==2 and
                        len(failing_tests)==2 and 
                        exit_code == 1)