import sys

sys.path.append('../')
sys.path.append('../../')
sys.path.append('../../../')

from mm.connection import PluginConnection

params = {
    "client"        : "SUBLIME_TEXT_3"
}
connection = PluginConnection(params)
print connection.sign_in_with_github({"username":"foo","password":"bar"})