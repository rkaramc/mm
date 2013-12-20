import unittest

from project.project_tests import ProjectTest
from unit_test.async_test_api import ApexUnitTestingTest

def suite():
    test_classes = [ApexUnitTestingTest, ProjectTest]
    suite = unittest.TestSuite()
    for unit_test_class in test_classes:
        for method in dir(unit_test_class):
            if method.startswith("test"):
                suite.addTest(unit_test_class(method))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    test_suite = suite()
    runner.run (test_suite)

