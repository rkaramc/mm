#!/usr/bin/env python
import encodings
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os.path
import argparse
import inspect
import json
import lib.config as config
import lib.mm_util as util
import urllib
import yaml
from StringIO import StringIO
from lib.mm_connection import MavensMatePluginConnection
from lib.mm_client import MavensMateClient
from lib.mm_exceptions import MMException

class MavensMateRequest():
    
    def __init__(self, *args, **kwargs): 
        #redirect stdout so prints to STDOUT don't affect the api
        self.output = StringIO()
        self.saved_stdout = sys.stdout
        sys.stdout = self.output

        self.operation      = None
        self.args           = kwargs.get('args', {})
        self.unknown_args   = kwargs.get('unknown_args', [])
        self.payload        = kwargs.get('payload', {})
        self.operation_dict = {
            'new_project'                           : self.new_project,
            'edit_project'                          : self.edit_project,
            'upgrade_project'                       : self.upgrade_project,
            'compile_project'                       : self.compile_project,
            'clean_project'                         : self.clean_project,
            'new_metadata'                          : self.new_metadata,
            'refresh'                               : self.refresh,
            'compile'                               : self.compile_selected_metadata,
            'delete'                                : self.delete_selected_metadata,
            'get_active_session'                    : self.get_active_session,
            'update_credentials'                    : self.update_credentials,
            'execute_apex'                          : self.execute_apex,
            'deploy_to_server'                      : self.deploy_to_server,
            'deploy'                                : self.deploy_to_server,
            'unit_test'                             : self.run_unit_tests,
            'test'                                  : self.run_unit_tests,
            'test_async'                            : self.run_async_tests,
            'list_metadata'                         : self.list_metadata,
            'index_metadata'                        : self.index_metadata,
            'refresh_metadata_index'                : self.refresh_metadata_index,
            'get_indexed_metadata'                  : self.get_metadata_index,
            'list_connections'                      : self.list_connections,
            'new_connection'                        : self.new_connection,
            'delete_connection'                     : self.delete_connection,
            'index_apex_overlays'                   : self.index_apex_overlays,
            'new_apex_overlay'                      : self.new_apex_overlay,
            'delete_apex_overlay'                   : self.delete_apex_overlay,
            'fetch_logs'                            : self.fetch_logs,
            'fetch_checkpoints'                     : self.fetch_checkpoints,
            'new_project_from_existing_directory'   : self.new_project_from_existing_directory,
            'open_sfdc_url'                         : self.open_sfdc_url,
            'get_symbols'                           : self.get_symbol_table,
            'index_apex_file_properties'            : self.index_apex_file_properties,
            'index_apex'                            : self.index_apex_file_properties,
            'update_subscription'                   : self.update_subscription,
            'new_log'                               : self.new_trace_flag,
            'new_quick_log'                         : self.new_quick_trace_flag,
            'update_debug_settings'                 : self.update_debug_settings,
            'eval'                                  : self.eval_function,
            'sign_in_with_github'                   : self.sign_in_with_github,
            'project_health_check'                  : self.project_health_check,
            'open_file_in_client'                   : self.open_file_in_client,
            'run_apex_script'                       : self.run_apex_script,
            'reset_metadata_container'              : self.reset_metadata_container
        }
        
        #determine operation
        if self.payload != None and 'operation' in self.payload:
            self.operation = self.payload['operation']
        elif self.args.operation != None:
            self.operation = self.args.operation
        elif self.unknown_args != [] and self.unknown_args[0] in self.operation_dict:
            self.operation = self.unknown_args[0]
        if self.operation == None:
            raise MMException('Unsupported operation')

    # each operation sets up a single connection
    # the connection holds information about the plugin running it
    # and establishes a project object
    def setup_connection(self):
        config.connection = MavensMatePluginConnection(
            client=self.args.client or 'SUBLIME_TEXT_3',
            ui=self.args.ui_switch,
            params=self.payload,
            operation=self.operation,
            verbose=self.args.verbose)

    def execute(self):
        try:
            self.setup_connection()
        except Exception as e:
            return util.generate_error_response(e.message)

        #if the arg switch argument is included, the request is to launch the out of box
        #MavensMate UI, so we generate the HTML for the UI and launch the process
        #example: mm -o new_project --ui
        if self.args.ui_switch == True:
            tmp_html_file = util.generate_ui(self.operation,self.payload)
            util.launch_ui(tmp_html_file)
            return util.generate_success_response('UI Generated Successfully')
        else:        
            config.logger.debug(self.operation)
            if self.operation not in self.operation_dict:
                raise MMException('Unsupported operation')
            requested_function = self.operation_dict[self.operation]
            return requested_function()

    # echo '{ "username" : "", "password" : "", "metadata_type" : "ApexClass" ' | joey2 mavensmate.py -o 'list_metadata'
    def list_metadata(self):
        if 'sid' in self.payload:
            client = MavensMateClient(credentials={
                "sid"                   : self.payload.get('sid', None),
                "metadata_server_url"   : urllib.unquote(self.payload.get('metadata_server_url', None)),
                "server_url"            : urllib.unquote(self.payload.get('server_url', None)),
            }) 
        elif 'username' in self.payload:
            client = MavensMateClient(credentials={
                "username"              : self.payload.get('username', None),
                "password"              : self.payload.get('password', None),
                "org_type"              : self.payload.get('org_type', None),
                "org_url"               : self.payload.get('org_url', None)
            })
        return json.dumps(client.list_metadata(self.payload['metadata_type']))

    def open_sfdc_url(self):
        return config.connection.project.open_selected_metadata(self.payload);

    def project_health_check(self):
        if self.args.respond_with_html == True:
            health_check_dict = config.connection.project.run_health_check();
            html = util.generate_html_response(self.operation, health_check_dict)
            return util.generate_success_response(html, "html")
        else:
            return json.dumps(config.connection.project.run_health_check(),indent=4);

    def list_connections(self):
        return config.connection.project.get_org_connections()

    def new_connection(self):
        return config.connection.project.new_org_connection(self.payload)

    def delete_connection(self):
        return config.connection.project.delete_org_connection(self.payload)

    def compile_selected_metadata(self):
        return config.connection.project.compile_selected_metadata(self.payload)

    def delete_selected_metadata(self):
        return config.connection.project.delete_selected_metadata(self.payload)

    def index_metadata(self):
        if 'metadata_type' in self.payload:
            index_result = config.connection.project.index_metadata(self.payload['metadata_type'])
        else:
            index_result = config.connection.project.index_metadata()
        if self.args.respond_with_html == True:
            html = util.generate_html_response(self.args.operation, index_result, self.payload)
            return util.generate_success_response(html, "html")
        else:
            return util.generate_success_response("Project metadata indexed successfully")

    def refresh_metadata_index(self):
        config.connection.project.index_metadata(self.payload['metadata_types'])
        return util.generate_success_response("Metadata refreshed successfully.")

    def get_metadata_index(self):
        if 'keyword' in self.payload or 'ids' in self.payload:
            return config.connection.project.filter_indexed_metadata(self.payload)
        elif 'package_name' in self.payload:
            return config.connection.project.get_org_metadata(True, True, package_name=self.payload["package_name"])
        else:
            #return config.connection.project.get_org_metadata(True, True)
            return config.connection.project.get_org_metadata(True, True)

    def new_project(self):
        return config.connection.new_project(self.payload,action='new')

    def new_project_from_existing_directory(self):
        return config.connection.new_project(self.payload,action='existing')

    def edit_project(self):
        return config.connection.project.edit(self.payload)

    def update_subscription(self):
        return config.connection.project.update_subscription(self.payload)

    def upgrade_project(self):
        return config.connection.project.upgrade()
        
    def compile_project(self):
        return config.connection.project.compile()

    def clean_project(self):
        return config.connection.project.clean()

    def refresh(self):
        return config.connection.project.refresh_selected_metadata(self.payload)

    def new_metadata(self):
        return config.connection.project.new_metadata(self.payload)

    def execute_apex(self):
        return config.connection.project.execute_apex(self.payload)

    def fetch_checkpoints(self):
        return config.connection.project.fetch_checkpoints(self.payload)

    def fetch_logs(self):
        return config.connection.project.fetch_logs(self.payload)

    def new_trace_flag(self):
        return config.connection.project.new_trace_flag(self.payload)

    def new_quick_trace_flag(self):
        return config.connection.project.new_quick_trace_flag()

    def update_debug_settings(self):
        return config.connection.project.update_debug_settings(self.payload)

    def run_apex_script(self):
        return config.connection.project.execute_apex(self.payload)

    # echo '{ "project_name" : "bloat", "classes" : [ "MyTester" ] }' | joey2 mavensmate.py -o 'test'
    def run_unit_tests(self):
        test_result = config.connection.project.run_unit_tests(self.payload)
        if self.args.respond_with_html ==  True:
            html = util.generate_html_response(self.operation, test_result, self.payload)
            return util.generate_success_response(html, "html")
        else:
            return test_result

    def run_async_tests(self):
        return config.connection.project.sfdc_client.run_async_apex_tests(self.payload)

    def deploy_to_server(self):
        deploy_result = config.connection.project.deploy_to_server(self.payload)
        if self.args.respond_with_html == True:
            html = util.generate_html_response(self.operation, deploy_result, self.payload)
            response = json.loads(util.generate_success_response(html, "html"))
            response['deploy_success'] = True
            # if deployment to one org fails, the entire deploy was not successful
            for result in deploy_result:
                if result['success'] == False:
                    response['deploy_success'] = False
                    break
            return json.dumps(response)
        else:
            return deploy_result

    # echo '{ "username" : "mm@force.com", "password" : "force", "org_type" : "developer" }' | joey2 mavensmate.py -o 'get_active_session'
    def get_active_session(self):
        try:
            if 'username' not in self.payload or self.payload['username'] == None or self.payload['username'] == '':
                raise MMException('Please enter a Salesforce.com username')
            if 'password' not in self.payload or self.payload['password'] == None or self.payload['password'] == '':
                raise MMException('Please enter a Salesforce.com password')
            if 'org_type' not in self.payload or self.payload['org_type'] == None or self.payload['org_type'] == '':
                raise MMException('Please select an org type')
            if 'org_type' in self.payload and self.payload['org_type'] == "custom" and "org_url" not in self.payload:
                raise MMException('To use a custom org type, please include a org_url parameter') 
            if 'org_type' in self.payload and self.payload['org_type'] == "custom" and "org_url" in self.payload and self.payload["org_url"] == "":
                raise MMException('Please specify the org url')    

            client = MavensMateClient(credentials={
                "username" : self.payload['username'],
                "password" : self.payload['password'],
                "org_type" : self.payload['org_type'],
                "org_url"  : self.payload.get('org_url', None)
            }) 
            
            response = {
                "sid"                   : client.sid,
                "user_id"               : client.user_id,
                "metadata_server_url"   : client.metadata_server_url,
                "server_url"            : client.server_url,
                "metadata"              : client.get_org_metadata(subscription=self.payload.get('subscription', None)),
                "success"               : True
            }
            return util.generate_response(response)
        except BaseException, e:
            return util.generate_error_response(e.message)

    def index_apex_overlays(self):
        return config.connection.project.index_apex_overlays(self.payload)

    def new_apex_overlay(self):
        return config.connection.project.new_apex_overlay(self.payload)

    def delete_apex_overlay(self):
        return config.connection.project.delete_apex_overlay(self.payload)

    def update_credentials(self):
        try:
            config.connection.project.username = self.payload['username']
            config.connection.project.password = self.payload['password']
            config.connection.project.org_type = self.payload['org_type']
            config.connection.project.org_url  = self.payload.get('org_url', None)
            config.connection.project.update_credentials()
            return util.generate_success_response('Your credentials were updated successfully')
        except BaseException, e:
            return util.generate_error_response(e.message)

    def get_symbol_table(self):
        return config.connection.project.get_symbol_table(self.payload)

    def index_apex_file_properties(self):
        return config.connection.project.index_apex_file_properties()

    def eval_function(self):
        python_request = self.payload['python']
        return eval(python_request)

    def sign_in_with_github(self):
        return config.connection.sign_in_with_github(self.payload)

    def open_file_in_client(self):
        return config.connection.project.open_file_in_client(self.payload)

    def reset_metadata_container(self):
        return config.connection.project.reset_metadata_container(accept="json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--operation', help='The requested operation') #name of the operation being requested
    parser.add_argument('-c', '--client', help='The plugin client being used') #name of the plugin client ("SUBLIME_TEXT_2", "SUBLIME_TEXT_3", "TEXTMATE", "NOTEPAD_PLUS_PLUS", "BB_EDIT", etc.)
    parser.add_argument('--ui', action='store_true', default=False, 
        dest='ui_switch', help='Launch the default UI for the operation')
    parser.add_argument('--quiet', action='store_true', default=False, 
        dest='quiet', help='Suppresses mm.py output')
    parser.add_argument('--html', action='store_true', default=False, 
        dest='respond_with_html', help='Makes various commands return HTML')
    parser.add_argument('--v', '--verbose', action='store_true', default=False, 
        dest='verbose', help='Makes me really loud and annoying')
    args, unknown = parser.parse_known_args()
    payload = util.get_request_payload()
    try:
        r = MavensMateRequest(args=args, payload=payload, unknown_args=unknown)
        response = r.execute()

        r.output.close()
        sys.stdout = r.saved_stdout

        config.logger.debug('\n\n')
        config.logger.debug('---------------------')
        config.logger.debug('RESPONDING TO REQUEST')
        config.logger.debug('---------------------')
        config.logger.debug('\n')
        config.logger.debug(response)

        print response
    except Exception as e:
        print util.generate_error_response(e.message)

if  __name__ == '__main__':
    main()