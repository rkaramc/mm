import os
import mm.util as util
import mm.config as config
from mm.exceptions import *
from mm.basecommand import Command
from mm.sfdc_client import MavensMateClient

class GetActiveSessionCommand(Command):
    def execute(self):
        if 'username' not in self.params or self.params['username'] == None or self.params['username'] == '':
            raise MMException('Please enter a Salesforce.com username')
        if 'password' not in self.params or self.params['password'] == None or self.params['password'] == '':
            raise MMException('Please enter a Salesforce.com password')
        if 'org_type' not in self.params or self.params['org_type'] == None or self.params['org_type'] == '':
            raise MMException('Please select an org type')
        if 'org_type' in self.params and self.params['org_type'] == "custom" and "org_url" not in self.params:
            raise MMException('To use a custom org type, please include a org_url parameter') 
        if 'org_type' in self.params and self.params['org_type'] == "custom" and "org_url" in self.params and self.params["org_url"] == "":
            raise MMException('Please specify the org url')    

        client = MavensMateClient(credentials={
            "username" : self.params['username'],
            "password" : self.params['password'],
            "org_type" : self.params['org_type'],
            "org_url"  : self.params.get('org_url', None)
        }) 
        
        response = {
            "sid"                   : client.sid,
            "user_id"               : client.user_id,
            "metadata_server_url"   : client.metadata_server_url,
            "server_url"            : client.server_url,
            "metadata"              : client.get_org_metadata(subscription=self.params.get('subscription', None)),
            "success"               : True
        }
        return util.generate_response(response)

class IndexApexSymbolsCommand(Command):
    aliases=["index_apex","index_apex_file_properties"]
    """
        Updates symbol index for one or more Apex Classes. If files is not included or empty, will force a full refresh
    """
    def execute(self):
        return config.project.index_apex_symbols(self.params.get("files", None))

class ResetMetadataContainerCommand(Command):
    def execute(self):
        return config.project.reset_metadata_container(accept="json")

class OpenFileInClientCommand(Command):
    """
        Opens the requested files in the plugin client (Sublime Text, etc.)
    """
    def execute(self):
        file_name = self.params["file_name"]
        extension = util.get_file_extension_no_period(file_name)
        mtype = util.get_meta_type_by_suffix(extension)
        full_file_path = os.path.join(config.project.location, "src", mtype["directoryName"], file_name)
        params = {
            "project_name"  : config.project.project_name,
            "file_name"     : full_file_path,
            "line_number"   : self.params.get("line_number", 0)
        } 
        config.connection.run_subl_command("open_file_in_project", json.dumps(params))
        return util.generate_success_response("ok")

class ExecuteApexCommand(Command):
    aliases=["run_apex_script"]
    """
        executes a string of apex
    """
    def execute(self):
        if 'script_name' in self.params: #running an apex script
            self.params["body"] = util.get_file_as_string(os.path.join(config.project.location,"apex-scripts",self.params["script_name"]))
        if 'debug_categories' not in self.params and not os.path.isfile(os.path.join(config.project.location,"config",".apex_script")):
            self.params["debug_categories"] = [
                {
                    "category"  : "Apex_code",
                    "level"     :  "DEBUG"
                }
            ]
        elif os.path.isfile(os.path.join(config.project.location,"config",".apex_script")):
            log_settings = util.parse_json_from_file(os.path.join(config.project.location,"config",".apex_script"))
            categories = []
            levels = log_settings["levels"]
            for category in levels.keys():
                categories.append({
                    "category"  : category,
                    "level"     : levels[category]
                })
            self.params["debug_categories"] = categories
        elif 'debug_categories' not in self.params:
            self.params["debug_categories"] = [
                {
                    "category"  : "Apex_code",
                    "level"     :  "DEBUG"
                }
            ]
        return_log = self.params.get("return_log", True)

        execute_result = config.sfdc_client.execute_apex(self.params)
        result = {
            'column'                : execute_result['column'],
            'compileProblem'        : execute_result['compileProblem'],
            'compiled'              : execute_result['compiled'],
            'exceptionMessage'      : execute_result['exceptionMessage'],
            'exceptionStackTrace'   : execute_result['exceptionStackTrace'],
            'line'                  : execute_result['line'],
            'success'               : execute_result['success'],
        }
        if 'log' in execute_result and return_log:
            result['log'] = execute_result['log']
        if result['success']:
            log_apex = config.connection.get_plugin_client_setting('mm_log_anonymous_apex', False)
            if log_apex:
                location = config.project.log_anonymous_apex(self.params['body'], execute_result['log'], self.params.get("script_name", None))
                result["log_location"] = location
        return util.generate_response(result)

class SignInWithGithubCommand(Command):
    def execute(self):
        return config.connection.sign_in_with_github(self.params)