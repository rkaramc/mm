#TO RUN: joey2 project_operation_tests.py
import sys
import unittest
import mock
sys.path.append('../')
sys.path.append('../../')
import mm.util as util
import test_util as util
from test_helper import MavensMateTest
import mm       

class CLITest(MavensMateTest):
    def test_bad_operation_name(self): 
        stdin = {
            "project_name" : "bloat"
        }
        sys.argv = ['mm.py', '-o', 'new_project_bad', '--ui']
        self.set_stdin(stdin)
        mm.main()
        mm_response = self.output.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        print mm_json_response
        self.assertTrue(mm_json_response['success'] == False)
        self.assertTrue(mm_json_response['body'] == 'Unsupported operation')
        
if __name__ == '__main__':
    unittest.main()