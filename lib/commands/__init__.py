import inspect
import debug
import deploy
import metadata
import project
import unittest
import misc
import server
import re

command_list = {}

modules = [
    debug, deploy, metadata, project, unittest, misc, server
]

def camelCaseToUnderscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

for module in modules:
    for member in inspect.getmembers(module):
        if "Command" in member[0] and member[0] != "Command":
            name_set = False
            clz = member[1]
            for k in clz.__dict__.keys():
                if k == "name":
                    command_list[clz.__dict__["name"]] = member[1]
                    name_set = True
                if k == "aliases":
                    aliases = clz.__dict__["aliases"]
                    if type(aliases) is list and len(aliases) > 0:
                        for alias in aliases:
                            command_list[alias] = member[1]
            if not name_set:
                name = camelCaseToUnderscore(member[0].replace("Command",""))
                command_list[name] = member[1]
