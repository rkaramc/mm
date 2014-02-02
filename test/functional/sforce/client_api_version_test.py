import sys
import pprint

sys.path.append('../')

import lib.crawlJson as crawlJson
import lib.util as util
from lib.connection import PluginConnection


params = {
	"project_name" 	: "bloat",
	"client" 		: "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)

print connection.sfdc_api_version