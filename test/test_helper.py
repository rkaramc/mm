import os
import sys
import unittest
import mock
from StringIO import StringIO
import json
import test_util as util
sys.path.append('../')
from lib.mm_connection import MavensMatePluginConnection
import lib.mm_util as mm_util
import mm

class MavensMateTest(unittest.TestCase):
    def get_plugin_client_settings(self):
        settings = {}
        settings['default']     = mm_util.parse_json_from_file(os.path.join(os.path.dirname(__file__),"default_client_settings.json"))
        settings['user']        = mm_util.parse_json_from_file(os.path.join(os.path.dirname(__file__),"user_client_settings.json"))
        return settings

    def redirectStdOut(self):
        new_target = StringIO()
        sys.stdout = new_target
        return new_target

    def setUp(self):
        self.output = StringIO()
        self.saved_stdout = sys.stdout
        sys.stdout = self.output
        self.settings = self.get_plugin_client_settings()
        MavensMatePluginConnection.get_plugin_client_settings = mock.Mock(return_value=self.settings)

    def tearDown(self):
        self.output.close()
        sys.stdout = self.saved_stdout

    def dict_to_string(self, dict):
        return json.dumps(dict)

    def set_stdin(self, dict):
        sys.stdin = StringIO(self.dict_to_string(dict))

def create_project(name="unit test project", package=None):
    if package is None:
        package = { "ApexClass" : "*" } 
    stdin = {
        "project_name"  : name,
        "username"      : "mm@force.com",
        "password"      : "force",
        "org_type"      : "developer",
        "action"        : "new",
        "package"       : package
    }
    mm_util.get_request_payload = mock.Mock(return_value=stdin)
    sys.argv = ['mm.py', '-o', 'new_project']
    mm.main()

# if __name__ == '__main__':
#     unittest.main()

