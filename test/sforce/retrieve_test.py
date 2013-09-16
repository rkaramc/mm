import sys
import pprint

sys.path.append('../')
sys.path.append('../../')

from lib.mm_connection import MavensMatePluginConnection
from lib.mm_client import MavensMateClient

params = {
	"client" 		: "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)

client = MavensMateClient(credentials={
    "username" : 'joe@mavensconsulting.com.eventmgmt',
    "password" : 'Rg3skins',
    "org_type" : 'sandbox'
})

package = {
	"Workflow" 	: "*"
}

#r = client.list_metadata_basic('CustomObject')
#r = client.retrieve(package=package)
r = client.list_metadata("Workflow")
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(r)