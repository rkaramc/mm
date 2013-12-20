import os
import sys
import unittest
import mock
import shutil
sys.path.append('../')
sys.path.append('../../')
import lib.mm_util as mm_util
import test_util as util
from test_helper import MavensMateTest
import mm    

base_test_directory = os.path.dirname(os.path.dirname(__file__))

class ApexUnitTestingTest(MavensMateTest):
        
    def test_01_create_new_project(self): 
        stdin = {
            "project_name"  : "unit test project",
            "username"      : "mm@force.com",
            "password"      : "force",
            "org_type"      : "developer",
            "action"        : "new",
            "package"       : {
                "ApexClass" : ["CompileAndTest"]
            } 
        }
        mm_util.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'new_project']
        mm.main()
        mm_response = self.output.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue(mm_json_response['body'] == 'Project Retrieved and Created Successfully')
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'])))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'classes')))

    def test_02_run_tests_async(self): 
        stdin = {
            "project_name"  : "unit test project",
            "classes"       : ["CompileAndTest"]
        }
        mm_util.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'test_async']
        mm.main()
        mm_response = self.output.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        #print mm_json_response
        self.assertTrue(len(mm_json_response) == 1)
        self.assertTrue(mm_json_response[0]['Status'] == 'Completed')

    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
            shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))

if __name__ == '__main__':
    if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
        shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))
    unittest.main()
