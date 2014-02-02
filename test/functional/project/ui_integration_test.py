#TO RUN: joey2 project_operation_tests.py
import os
import sys
import unittest
import mock
import shutil
sys.path.append('../')
sys.path.append('../../')
sys.path.append('../../../')
import test_util as util
from lib.request import MavensMateRequestHandler
import test_helper
from test_helper import MavensMateTest
import lib.request as request

base_test_directory = test_helper.base_test_directory

class ProjectUiIntegrationTest(MavensMateTest):
        
    def test_01_get_active_session_bad_creds(self): 
        commandOut = self.redirectStdOut()
        stdin = {
            "username" : "mm@force.commm",
            "password" : "forceee",
            "org_type" : "developer"
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'get_active_session']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == False)
        self.assertTrue(mm_json_response['body'] == "Server raised fault: 'INVALID_LOGIN: Invalid username, password, security token; or user locked out.'")

    def test_02_get_active_session_bad_request(self): 
        commandOut = self.redirectStdOut()
        stdin = {
            "username" : "mm@force.com"
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'get_active_session']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == False)
        self.assertTrue(mm_json_response['body'] == "Please enter a Salesforce.com password")

    def test_03_get_active_session_good_creds(self): 
        commandOut = self.redirectStdOut()
        stdin = {
            "username" : "mm@force.com",
            "password" : "force",
            "org_type" : "developer"
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'get_active_session']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        print mm_json_response
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue(len(mm_json_response['user_id']) is 18)

    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
            shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))

if __name__ == '__main__':
    if os.path.exists(os.path.join(base_test_directory,"test_workspace","unit test project")):
        shutil.rmtree(os.path.join(base_test_directory,"test_workspace","unit test project"))
    unittest.main()