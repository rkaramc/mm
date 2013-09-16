import sys
import unittest
import os
import re
sys.path.append('../')
sys.path.append('../../')
import lib.mm_util as mm_util

import plyj.parser as plyj
import plyj.model as model
parser = plyj.Parser()

base_test_directory = os.path.dirname(os.path.dirname(__file__))
project_name = "unit test health check project"


class ApexParserTest(unittest.TestCase):
    def test_parse_for_loop(self): 
        #for_loop_pattern = re.compile(r"(for|while) *?\(.*?\).*?{.*?(insert|update|delete|upsert).*?;.*?}", re.IGNORECASE|re.MULTILINE|re.DOTALL)
        for_loop_pattern = re.compile(r"""(?:\s|^)for\s*\([^;{}]*;[^;{}]*;[^{}]*\)\s*\{\}""", re.IGNORECASE|re.MULTILINE|re.DOTALL)
        #for_loop_pattern = re.compile(r"for\s*\([^;]*?;[^;]*?;[^)]*?\)", re.IGNORECASE|re.MULTILINE|re.DOTALL)
        file_name = os.path.join(base_test_directory,"test_workspace",project_name,"src","classes","MyClass.cls")
        file_body = mm_util.get_file_as_string(file_name)
        print file_body
        tree = parser.parse_string(file_body)
        print tree
        # for_loop_matches = re.finditer(for_loop_pattern, file_body)          
        # matches = []
        # for match in for_loop_matches:
        #     matches.append(match.group(0))
        # print 'matches', len(matches)
        # print matches
        
if __name__ == '__main__':
    unittest.main()