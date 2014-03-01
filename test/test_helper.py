#from __future__ import absolute_import
import os.path
import sys
import unittest
import mock
from StringIO import StringIO
import test_util as util
sys.path.append('../')
import lib.request as request
from lib.request import MavensMateRequestHandler
from lib.connection import PluginConnection

base_test_directory = os.path.dirname(__file__)

class MavensMateTest(unittest.TestCase):

    def redirectStdOut(self):
        new_target = StringIO()
        sys.stdout = new_target
        return new_target

    def resetStdOut(self, redirect=False):
        sys.stdout = self.saved_stdout
        if redirect:
            self.redirectStdOut()

    def setUp(self):
        self.output = StringIO()
        self.saved_stdout = sys.stdout
        sys.stdout = self.output
        self.settings = util.get_plugin_client_settings()
        PluginConnection.get_plugin_client_settings = mock.Mock(return_value=self.settings)

    def tearDown(self):
        self.output.close()
        sys.stdout = self.saved_stdout

    def set_stdin(self, dict):
        sys.stdin = StringIO(util.dict_to_string(dict))

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
    request.get_request_payload = mock.Mock(return_value=stdin)
    sys.argv = ['mm.py', '-o', 'new_project', '-f', 'json']
    MavensMateRequestHandler().execute()
    return stdin

def edit_project(name="unit test project", package=None):
    if package is None:
        package = { "ApexClass" : "*" } 
    stdin = {
        "project_name"  : name,
        "package"       : package
    }
    request.get_request_payload = mock.Mock(return_value=stdin)
    sys.argv = ['mm.py', '-o', 'edit_project']
    MavensMateRequestHandler().execute()
    return stdin

def clean_project(name="unit test project"): 
    stdin = {
        "project_name"  : name
    }
    request.get_request_payload = mock.Mock(return_value=stdin)
    sys.argv = ['mm.py', '-o', 'clean_project']
    MavensMateRequestHandler().execute()
    return stdin

def compile(name="unit test project", files=[]): 
    stdin = {
        "project_name"  : name,
        "files"         : files
    }
    request.get_request_payload = mock.Mock(return_value=stdin)
    sys.argv = ['mm.py', '-o', 'compile']
    MavensMateRequestHandler().execute()
    return stdin

def compile_project(name="unit test project"): 
    stdin = {
        "project_name"  : name
    }
    request.get_request_payload = mock.Mock(return_value=stdin)
    sys.argv = ['mm.py', '-o', 'compile_project']
    MavensMateRequestHandler().execute()
    return stdin

def create_apex_metadata(project_name, metadata_type="ApexClass", api_name="unittestapexclass"):
    stdin = {
        "github_template": {
            "author"        : "MavensMate", 
            "description"   : "The default template for an Apex Class", 
            "name"          : "Default", 
            "file_name"     : "ApexClass.cls"
        }, 
        "apex_trigger_object_api_name"  : None, 
        "apex_class_type"               : None, 
        "api_name"                      : api_name, 
        "project_name"                  : project_name, 
        "metadata_type"                 : metadata_type
    }
    request.get_request_payload = mock.Mock(return_value=stdin)
    sys.argv = ['mm.py', '-o', 'new_metadata']
    MavensMateRequestHandler().execute()

def delete_apex_metadata(project_name, files=[], dirs=[]):
   stdin = {
       "files": files, 
       "project_name": project_name
   }
   request.get_request_payload = mock.Mock(return_value=stdin)
   sys.argv = ['mm.py', '-o', 'delete']
   MavensMateRequestHandler().execute()



