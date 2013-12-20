import sys
import pprint

sys.path.append('../')
sys.path.append('../../')

from lib.mm_connection import MavensMatePluginConnection


params = {
	"project_name" 	: "joeferraro4",
	"client" 		: "SUBLIME_TEXT_3",
    "workspace"     : "/Users/josephferraro/Development/st"
}
connection = MavensMatePluginConnection(params)
r = connection.project.get_org_metadata(False, True)

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(r[4])