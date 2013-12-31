import unittest

from project.project_tests import ProjectTest
from unit_test.async_test_api import ApexUnitTestingTest
from metadata.create_tests import MetadataOperationTest
from tooling.checkpoint_tests import CheckpointTests
from tooling.log_tests import StackTraceAndLogsTest
from metadata.refresh_tests import MetadataRefreshTest
from project.ui_integration_test import ProjectUiIntegrationTest

def suite():
    test_classes = [
        ApexUnitTestingTest, 
        ProjectTest, 
        MetadataOperationTest, 
        MetadataRefreshTest, 
        CheckpointTests,
        StackTraceAndLogsTest,
        ProjectUiIntegrationTest
    ]
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

