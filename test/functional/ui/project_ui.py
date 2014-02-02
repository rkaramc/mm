import sys
import unittest
import os
sys.path.append('../')
sys.path.append('../../')
import test_util as util
from test_helper import MavensMateTest
import mm     

class UITest(MavensMateTest):
    def test_project_ui(self): 
        stdin = {}
        sys.argv = ['mm.py', '-o', 'new_project', '--ui']
        self.set_stdin(stdin)
        mm.main()
        mm_response = self.output.getvalue()
        sys.stdout = self.saved_stdout
        mm_json_response = util.parse_mm_response(mm_response)
        print mm_json_response
        self.assertTrue(mm_json_response['success'] == True)

    def tearDown(self):
        os.system('killAll MavensMateWindowServer')

if __name__ == '__main__':
    unittest.main()

