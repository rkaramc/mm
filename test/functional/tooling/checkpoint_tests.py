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

class CheckpointTests(MavensMateTest):
 
    def test_01_new_debug_log(self): 
        test_helper.create_project("unit test tooling project")
        commandOut = self.redirectStdOut()
        stdin = {
            "project_name"      : "unit test tooling project",
            "type"              : "user",
            "debug_categories"  : {
                "ApexCode"      : "DEBUG",
                "Visualforce"   : "DEBUG"
            }
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'new_log']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue('id' in mm_json_response and len(mm_json_response['id']) is 18)

    def test_02_new_apex_checkpoint(self): 
        test_helper.create_project("unit test tooling project")
        commandOut = self.redirectStdOut()

        ###CREATE APEX CLASS
        # stdin = {
        #     "github_template": {
        #         "author": "MavensMate", 
        #         "description": "The default template for an Apex Class", 
        #         "name": "Default", 
        #         "file_name": "ApexClass.cls"
        #     }, 
        #     "apex_trigger_object_api_name": None, 
        #     "apex_class_type": None, 
        #     "api_name": "unittesttoolingapexclass", 
        #     "project_name": "unit test tooling project", 
        #     "metadata_type": "ApexClass"
        # }
        stdin = {
            'project_name' : 'unit test tooling project',
            'metadata_type': 'ApexClass', 
            'params': {'api_name': 'unittesttoolingapexclass'}, 
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
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue('id' in mm_json_response and len(mm_json_response['id']) is 18)

        ###CREATE CHECKPOINT
        stdin = {
            "project_name"      : "unit test tooling project",
            "IsDumpingHeap"     : True, 
            "Iteration"         : 1, 
            "Object_Type"       : "ApexClass", 
            "Line"              : 1,
            "ActionScriptType"  : "None", 
            "API_Name"          : "unittesttoolingapexclass"
        }
        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'new_apex_overlay']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)
        self.assertTrue('id' in mm_json_response and len(mm_json_response['id']) is 18)

        ###DELETE CLASS
        client_settings = util.parse_json_from_file(os.path.join(test_helper.base_test_directory, "user_client_settings.json"))
        stdin = {
            "files": [os.path.join(client_settings["mm_workspace"],"unit test tooling project","src","classes","unittesttoolingapexclass.cls")], 
            "project_name": "unit test tooling project"
        }

        request.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'delete']
        MavensMateRequestHandler().execute()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        mm_json_response = util.parse_mm_response(mm_response)
        self.assertTrue(mm_json_response['success'] == True)


    @classmethod    
    def tearDownClass(self):
        if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test tooling project")):
            shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test tooling project"))

if __name__ == '__main__':
    if os.path.exists(os.path.join(test_helper.base_test_directory,"test_workspace","unit test tooling project")):
        shutil.rmtree(os.path.join(test_helper.base_test_directory,"test_workspace","unit test tooling project"))
    unittest.main()