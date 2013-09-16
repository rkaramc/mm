import sys
import pprint

sys.path.append('../')

import lib.mm_github as github
from lib.mm_connection import MavensMatePluginConnection

params = {
    "client"        : "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)
print connection.sign_in_with_github({"username":"foo","password":"bar"})