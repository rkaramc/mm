import unittest

from functional.project.project_tests import ProjectTest
from functional.unit_test.async_test_api import ApexUnitTestingTest
from functional.metadata.create_tests import MetadataOperationTest
from functional.tooling.checkpoint_tests import CheckpointTests
from functional.tooling.log_tests import StackTraceAndLogsTest
from functional.metadata.refresh_tests import MetadataRefreshTest
from functional.project.ui_integration_test import ProjectUiIntegrationTest
from functional.metadata.compilation_tests import CompilationTests


def suite():
    test_classes = [
        ApexUnitTestingTest, 
        ProjectTest, 
        MetadataOperationTest, 
        MetadataRefreshTest, 
        CheckpointTests,
        StackTraceAndLogsTest,
        ProjectUiIntegrationTest,
        CompilationTests
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

