import sys
import pprint

sys.path.append('../')

import lib.crawlJson as crawlJson
import lib.mm_util as util
from lib.mm_connection import MavensMatePluginConnection


params = {
    "project_name"  : "managed test",
    "client"        : "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)
resp = connection.project.sfdc_client.delete_mavensmate_metadatacontainers_for_this_user()
print resp

resp = connection.project.sfdc_client.new_metadatacontainer_for_this_user()
print resp
