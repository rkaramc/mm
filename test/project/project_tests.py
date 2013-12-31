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
import test_helper
from test_helper import MavensMateTest
import mm    

base_test_directory = os.path.dirname(os.path.dirname(__file__))

class ProjectTest(MavensMateTest):
        
    def test_01_create_new_project(self): 
        package = {
            "ApexClass" : "*",
            "ApexPage"  : "*",
            "Report"    : [],
            "Document"  : []
        }
        stdin = test_helper.create_project("unit test project", package=package)
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
        stdin = test_helper.edit_project("unit test project", package={ "ApexClass" : "*" } )
        mm_response = self.output.getvalue()
        mm_json_response = util.parse_mm_response(mm_response)
        sys.stdout = self.saved_stdout
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue(mm_json_response['body'] == 'Project Edited Successfully')
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'])))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'classes')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'pages')))
        #self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'reports'))) TODO: why is this failing?
        #self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'documents')))

    def test_03_clean_project(self):
        stdin = test_helper.clean_project("unit test project")
        mm_response = self.output.getvalue()
        mm_json_response = util.parse_mm_response(mm_response)
        sys.stdout = self.saved_stdout
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue(mm_json_response['body'] == 'Project Cleaned Successfully')
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'])))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'classes')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'pages')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'reports')))
        self.assertFalse(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'documents')))

    def test_04_compile_project(self):
        stdin = test_helper.compile_project("unit test project")
        mm_response = self.output.getvalue()
        mm_json_response = util.parse_mm_response(mm_response)
        sys.stdout = self.saved_stdout
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'])))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'classes')))
        self.assertTrue(os.path.exists(os.path.join(base_test_directory, 'test_workspace', stdin['project_name'], 'src', 'package.xml')))

    def test_05_update_project_subscription(self):
        commandOut = self.redirectStdOut()
        stdin = {
            "subscription" : ["ApexPage","ApexComponent"], 
            "project_name" : "unit test project" 
        }
        mm_util.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'update_subscription']
        mm.main()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        project_settings = util.parse_json_file(os.path.join(base_test_directory, 'test_workspace', 'unit test project', 'config', '.settings'))
        self.assertTrue(type(project_settings['subscription']) is list and len(project_settings['subscription']) == 2)
        self.assertTrue(project_settings['subscription'][0] == "ApexPage")
        self.assertTrue(project_settings['subscription'][1] == "ApexComponent")


    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
            shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))

if __name__ == '__main__':
    if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
        shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))
    unittest.main()