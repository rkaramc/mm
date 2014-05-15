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
from lib.request import MavensMateRequestHandler
import lib.request as request
import lib.util as mmutil

class MetadataOperationTest(MavensMateTest):
    
    def test_01_new_apex_class(self): 
        test_helper.create_project("unit test metadata project")
        commandOut = self.redirectStdOut()
        # stdin = {
        #     "github_template": {
        #         "author": "MavensMate", 
        #         "description": "The default template for an Apex Class", 
        #         "name": "Default", 
        #         "file_name": "ApexClass.cls"
        #     }, 
        #     "apex_trigger_object_api_name": None, 
        #     "apex_class_type": None, 
        #     "api_name": "unittestapexclass", 
        #     "project_name": "unit test metadata project", 
        #     "metadata_type": "ApexClass"
        # }
        stdin = {
            'project_name' : 'unit test metadata project',
            'metadata_type': 'ApexClass', 
            'params': {'api_name': 'unittestapexclass'}, 
            'github_template': {
                'author': 'MavensMate', 
                'name': 'Default', 
                'description': 'The default template for an Apex Class', 
                'file_name': 'ApexClass.cls', 
                'params': [
                    {
                        'default': 'MyApexClass', 
                        'name': 'api_name', 
                        'description': 'Apex Class API Name'
                    }
                ]
            }
        }

        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'new_metadata']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = test_util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue('id' in mm_json_response and len(mm_json_response['id']) is 18)

    def test_02_compile_apex_class(self): 
        test_helper.create_project("unit test metadata project")
        commandOut = self.redirectStdOut()
        client_settings = mmutil.parse_json_from_file(os.path.join(test_helper.base_test_directory, "user_client_settings.json"))
        stdin = {
            "project_name": "unit test metadata project", 
            "files": [os.path.join(client_settings["mm_workspace"],"unit test metadata project","src","classes","unittestapexclass.cls")] 
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'compile']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = test_util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['State'] == "Completed")
        self.assertTrue(mm_json_response['ErrorMsg'] == None)

    def test_03_delete_apex_class(self): 
        commandOut = self.redirectStdOut()
        client_settings = mmutil.parse_json_from_file(os.path.join(test_helper.base_test_directory, "user_client_settings.json"))
        stdin = {
            "files": [os.path.join(client_settings["mm_workspace"],"unit test metadata project","src","classes","unittestapexclass.cls")], 
            "project_name": "unit test metadata project"
        }

        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'delete']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = test_util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)

    # def test_02_new_quicklog(self): 
    #     commandOut = self.redirectStdOut()
    #     stdin = {
    #         "project_name"      : "unit test tooling project",
    #         "type"              : "user",
    #         "debug_categories"  : {
    #             "ApexCode"      : "DEBUG",
    #             "Visualforce"   : "INFO"
    #         }
    #     }
    #     request.get_request_payload = mock.Mock(return_value=stdin)
    #     sys.argv = ['mm.py', '-o', 'new_quick_log']
    #     MavensMateRequestHandler().execute()
    #     mm_response = commandOut.getvalue()
    #     sys.stdout = self.saved_stdout
    #     print mm_response
    #     mm_json_response = test_util.parse_mm_response(mm_response)
    #     self.assertTrue(mm_json_response['success'] == True)
    #     self.assertTrue('1 Log(s) created successfully' in mm_json_response['body'])

    # def test_03_update_debug_settings(self): 
    #     commandOut = self.redirectStdOut()
    #     stdin = {
    #         "project_name"      : "unit test tooling project",
    #         "debug_categories"  : {
    #             "Workflow"      : "FINE", 
    #             "Callout"       : "FINE", 
    #             "System"        : "FINE", 
    #             "Database"      : "FINE", 
    #             "ApexCode"      : "FINE", 
    #             "Validation"    : "FINE", 
    #             "Visualforce"   : "FINE"
    #         },
    #         "expiration"        : 120
    #     }
    #     request.get_request_payload = mock.Mock(return_value=stdin)
    #     sys.argv = ['mm.py', '-o', 'update_debug_settings']
    #     MavensMateRequestHandler().execute()
    #     mm_response = commandOut.getvalue()
    #     sys.stdout = self.saved_stdout
    #     print mm_response
    #     mm_json_response = test_util.parse_mm_response(mm_response)
    #     new_debug_settings = test_util.parse_json_file(os.path.join(test_helper.base_test_directory, "test_workspace", stdin["project_name"], "config", ".debug"))
    #     self.assertTrue(new_debug_settings['expiration'] == stdin["expiration"])
    #     self.assertTrue(new_debug_settings['levels']['Workflow'] == stdin["debug_categories"]["Workflow"])
    #     self.assertTrue(new_debug_settings['levels']['Visualforce'] == stdin["debug_categories"]["Visualforce"])

    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test metadata project")):
           shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test metadata project"))
        #pass

if __name__ == '__main__':
    if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test metadata project")):
        shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test metadata project"))
    unittest.main()