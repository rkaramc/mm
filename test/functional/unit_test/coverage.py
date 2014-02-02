import os
import sys
import unittest
import mock
import shutil
sys.path.append('../')
sys.path.append('../../')
sys.path.append('../../../')
import mm.util as util
import test_util as test_util
import test_helper
from test_helper import MavensMateTest
from mm.request import MavensMateRequestHandler
import mm.request as request

class ApexUnitTestCoverageTest(MavensMateTest):
        
    def test_01_get_coverage(self): 
        test_helper.create_project("unit test project", package={ "ApexClass" : "*" })
        commandOut = self.redirectStdOut()
        stdin = {
            "project_name"  : "unit test project"
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'code_coverage_report']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = test_util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['totalSize'] > 0)
        self.assertTrue(mm_json_response['done'] == True)
        self.assertTrue(mm_json_response['entityTypeName'] == "ApexCodeCoverageAggregate")

        



    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test project")):
            shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test project"))

if __name__ == '__main__':
    if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test project")):
        shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test project"))
    unittest.main()
