#TO RUN: joey2 project_operation_tests.py
import os
import sys
import unittest
import mock
import shutil
sys.path.append('../')
sys.path.append('../../')
sys.path.append('../../../')
import test_util as test_util
import test_helper
from test_helper import MavensMateTest
from mm.request import MavensMateRequestHandler
import mm.request as request
import mm.util as mmutil

class MetadataOperationTest(MavensMateTest):
    
    def test_01_new_org_connection(self): 
        test_helper.create_project("unit test deploy project")
        commandOut = self.redirectStdOut()
        stdin = {
            "username"      : "mm@force.com",
            "password"      : "force",
            "org_type"      : "developer",
            "project_name"  : "unit test deploy project"
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'new_connection']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = test_util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)

    def test_02_deploy(self): 
        commandOut = self.redirectStdOut()
        client_settings = mmutil.parse_json_from_file(os.path.join(test_helper.base_test_directory, "user_client_settings.json"))
        org_connections = test_util.parse_json_from_file(os.path.join(client_settings["mm_workspace"],"unit test deploy project","config",".org_connections"))
        stdin = {
            "project_name"      :   "unit test deploy project",
            "destinations"      :   [
                {
                    "id"            : org_connections[0]["id"],
                    "username"      : org_connections[0]["username"],
                    "org_type"      : org_connections[0]["environment"]
                }
            ],
            "check_only"        :   True,
            "run_tests"         :   False,
            "rollback_on_error" :   True,
            "package"           :   {
                "ApexClass" : ["CompileAndTest"]
            },
            "debug_categories"  :   ""
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'deploy', '--html']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = test_util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)

    def test_03_delete_org_connection(self): 
        commandOut = self.redirectStdOut()
        client_settings = mmutil.parse_json_from_file(os.path.join(test_helper.base_test_directory, "user_client_settings.json"))
        org_connections = test_util.parse_json_from_file(os.path.join(client_settings["mm_workspace"],"unit test deploy project","config",".org_connections"))
        stdin = {
            "id"            : org_connections[0]["id"],
            "project_name"  : "unit test deploy project"
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'delete_connection']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = test_util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)


    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test deploy project")):
           shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test deploy project"))
        #pass

if __name__ == '__main__':
    if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test deploy project")):
        shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test deploy project"))
    unittest.main()