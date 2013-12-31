import json
import os
import lib.mm_util as mm_util

def parse_mm_response(json_string):
    return json.loads(json_string)

def parse_json_string(json_string):
    return json.loads(json_string)

def parse_json_file(location):
    if not os.path.exists(location):
        return {}
    json_data = open(location)
    if json_data:
        data = json.load(json_data)
        json_data.close()
        return data

def dict_to_string(self, dict):
    return json.dumps(dict)

def get_plugin_client_settings():
    settings = {}
    settings['default']     = mm_util.parse_json_from_file(os.path.join(os.path.dirname(__file__),"default_client_settings.json"))
    settings['user']        = mm_util.parse_json_from_file(os.path.join(os.path.dirname(__file__),"user_client_settings.json"))
    return settings