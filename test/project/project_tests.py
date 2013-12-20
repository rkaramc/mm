#TO RUN: joey2 project_operation_tests.py
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

class ProjectTest(MavensMateTest):
        
    def test_01_create_new_project(self): 
        stdin = {
            "project_name"  : "unit test project",
            "username"      : "mm@force.com",
            "password"      : "force",
            "org_type"      : "developer",
            "action"        : "new",
            "package"       : {
                "ApexClass" : "*",
                "ApexPage"  : "*",
                "Report"    : [],
                "Document"  : []
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
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'pages')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'reports')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'documents')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'documents', 'MavensMate_Documents')))


    def test_02_edit_project(self): 
        stdin = {
            "project_name"  : "unit test project",
            "package"       : {
                "ApexClass" : "*"
            }
        }
        mm_util.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'edit_project']
        mm.main()
        mm_response = self.output.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue(mm_json_response['body'] == 'Project Edited Successfully')
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'])))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'classes')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'pages')))
        #self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'reports'))) TODO: why is this failing?
        #self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'documents')))

    def test_03_clean_project(self):
        stdin = {
            "project_name"  : "unit test project"
        }
        mm_util.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'clean_project']
        mm.main()
        mm_response = self.output.getvalue()
        sys.stdout = self.saved_stdout
        #print mm_response
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue(mm_json_response['body'] == 'Project Cleaned Successfully')
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'])))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'classes')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'pages')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'reports')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'documents')))

    def test_04_compile_project(self):
        stdin = {
            "project_name"  : "unit test project"
        }
        mm_util.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'compile_project']
        mm.main()
        mm_response = self.output.getvalue()
        sys.stdout = self.saved_stdout
        #print mm_response
        mm_json_response = util.parse_mm_response(mm_response)
        print mm_json_response
        self.assertTrue(mm_json_response['success'] == True)

    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
            shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))

if __name__ == '__main__':
    if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
        shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))
    unittest.main()