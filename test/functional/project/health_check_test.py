#TO RUN: joey2 project_operation_tests.py
import os
import sys
import unittest
import mock
import shutil
sys.path.append('../')
sys.path.append('../../')
import mm.util as util
import test_util as util
import test_helper
from test_helper import MavensMateTest
import mm    
import mm.sfdc_client as sfdc

base_test_directory = os.path.dirname(os.path.dirname(__file__))
project_name = "unit test health check project"

class ProjectHealthCheckTests(MavensMateTest):
    
    def test_01_new_health_check(self): 
        if not os.path.exists(os.path.join(base_test_directory,"test_workspace",project_name)):
            package = {
                "ApexClass"     : "*",
                "ApexTrigger"   : "*",
                "ApexPage"      : "*"
            }
            test_helper.create_project(project_name, package)
        commandOut = self.redirectStdOut()
        stdin = {
            "project_name"      : project_name,
            "type"              : "user",
            "debug_categories"  : {
                "ApexCode"      : "DEBUG",
                "Visualforce"   : "INFO"
            }
        }
        util.get_request_payload = mock.Mock(return_value=stdin)
        sys.argv = ['mm.py', '-o', 'project_health_check']
        mm.main()
        mm_response = commandOut.getvalue()
        sys.stdout = self.saved_stdout
        print mm_response
        #mm_json_response = util.parse_mm_response(mm_response)
        
   
    @classmethod    
    def tearDownClass(self):
        # if os.path.exists(os.path.join(base_test_directory,"test_workspace",project_name)):
        #    shutil.rmtree(os.path.join(base_test_directory,"test_workspace",project_name))
        pass

if __name__ == '__main__':
    # if os.path.exists(os.path.join(base_test_directory,"test_workspace",project_name)):
    #     shutil.rmtree(os.path.join(base_test_directory,"test_workspace",project_name))
    unittest.main()