import sys
import pprint
import json
sys.path.append('../')
sys.path.append('../../')

from lib.connection import PluginConnection

params = {
	"project_name" 	: "prereltest",
	"client" 		: "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)
resp = connection.project.sfdc_client.get_completions('String')
#obj = json.loads(resp)
#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(obj)
print resp

