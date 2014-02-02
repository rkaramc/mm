import json
import os
import lib.util as util
import re

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
    settings['default']     = util.parse_json_from_file(os.path.join(os.path.dirname(__file__),"default_client_settings.json"))
    settings['user']        = util.parse_json_from_file(os.path.join(os.path.dirname(__file__),"user_client_settings.json"))
    return settings

def parse_json_from_file(location):
    if not os.path.exists(location):
        return {}
    try:
        json_data = open(location)
        if json_data:
            data = json.load(json_data)
            json_data.close()
            return data
    except:
        return parse_json(location)

def parse_json(filename):
    """ Parse a JSON file
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """
    # Regular expression for comments
    comment_re = re.compile(
        '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
        re.DOTALL | re.MULTILINE
    )

    with open(filename) as f:
        content = ''.join(f.readlines())

        ## Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)

        # Return json file
        return json.loads(content)