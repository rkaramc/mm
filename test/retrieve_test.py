import sys
import pprint

sys.path.append('../')

import lib.crawlJson as crawlJson
import lib.mm_util as util
from lib.mm_connection import MavensMatePluginConnection
from lib.mm_client import MavensMateClient

params = {
	"client" 		: "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)

client = MavensMateClient(credentials={
    "username" : 'mm@force.com',
    "password" : 'force',
    "org_type" : 'developer'
})

package = {
	"CustomObject" 	: "*",
	"Profile" 		: "*"
}

#r = client.list_metadata_basic('CustomObject')
r = client.retrieve(package=package)
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(r)