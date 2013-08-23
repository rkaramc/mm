import sys
import pprint

sys.path.append('../')

import lib.crawlJson as crawlJson
import lib.mm_util as util
from lib.mm_connection import MavensMatePluginConnection


params = {
    "project_name"  : "bloat",
    "client"        : "SUBLIME_TEXT_3",
    "classes"       : ["CompileAndTest"]
}
connection = MavensMatePluginConnection(params)
resp = connection.project.sfdc_client.run_async_apex_tests(params["classes"])

pp = pprint.PrettyPrinter(indent=2)
pp.pprint(resp)
