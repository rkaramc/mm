import sys
import pprint

sys.path.append('../')

import lib.crawlJson as crawlJson
import mm.util as util
from mm.connection import PluginConnection

# src = [
# 	{ 
# 		"text" : "ApexClass",
# 		"children" : [
# 			{
# 				"text" 		: "MyCoolClass",
# 				"checked" 	: True
# 			}
# 		]
# 	},
# 	{ 
# 		"text" : "ApexPage",
# 		"children" : [
# 			{
# 				"text" 		: "MyPage",
# 				"checked" 	: False
# 			},
# 			{
# 				"text" 		: "A Different Page",
# 				"checked" 	: True
# 			}
# 		]
# 	}
# ]
params = {
	"project_name" 	: "bloat",
	"client" 		: "SUBLIME_TEXT_2"
}
connection = MavensMatePluginConnection(params)
resp = connection.project.get_org_metadata(False, True)

pp = pprint.PrettyPrinter(indent=4)
pp.pprint(resp[1])


