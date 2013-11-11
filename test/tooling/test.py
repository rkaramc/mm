import sys
import pprint
import requests
import urllib
sys.path.append('../')
sys.path.append('../../')
from lib.mm_connection import MavensMatePluginConnection

params = {
    "project_name"  : "mercury-force",
    "client"        : "SUBLIME_TEXT_3",
    "workspace"     : "/Users/josephferraro/Development/st"
}
connection = MavensMatePluginConnection(params)
client = connection.project.sfdc_client

query_string = "Select Id, Name, CreatedDate from MetadataContainer"
r = requests.get(client.get_tooling_url()+"/query/", params={'q':query_string}, headers=client.get_rest_headers(), proxies=urllib.getproxies(), verify=False)
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(r.text)

#print client.delete_mavensmate_metadatacontainers_for_this_user()
#print client.new_metadatacontainer_for_this_user()
