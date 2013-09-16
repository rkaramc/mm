import json
import os

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

