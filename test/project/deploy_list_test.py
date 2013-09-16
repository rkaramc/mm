import sys
import pprint


sys.path.append('../')
sys.path.append('../../')

from lib.mm_connection import MavensMatePluginConnection


params = {
    "project_name"  : "Astellas Event Dev Box",
    "client"        : "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)
resp = connection.project.get_deployment_names()
print resp
