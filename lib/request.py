import sys
import argparse
import util
import json
import config
import pprint
from exceptions import *
from connection import PluginConnection
from project import MavensMateProject
from StringIO import StringIO
import lib.commands

pp = pprint.PrettyPrinter(indent=2)
debug = config.logger.debug

class MavensMateRequestHandler():
    
    def __init__(self, *args, **kwargs): 
        #self.__redirect_stdout()       
        self.args, self.unknown_args    = parse_args()
        self.operation                  = None
        self.response_format            = self.args.format
        self.payload                    = get_request_payload()
        self.__set_operation()

    def __redirect_stdout(self):
        #redirect stdout so prints to STDOUT don't affect the api
        self.output = StringIO()
        self.saved_stdout = sys.stdout
        sys.stdout = self.output

    def __set_operation(self):
        if self.payload != None and 'operation' in self.payload:
            self.operation = self.payload['operation']
        elif self.args.operation != None:
            self.operation = self.args.operation
        elif self.unknown_args != [] and self.unknown_args[0]:
            self.operation = self.unknown_args[0]
        if self.operation == None:
            raise MMException('Unsupported operation')

    def __setup_connection(self):
        """        
            each operation requested represents a session
            the session holds information about the plugin running it
            and establishes a project object
        """        
        config.connection = PluginConnection(
            client=self.args.client or 'SUBLIME_TEXT_3',
            ui=self.args.ui_switch,
            args=self.args,
            params=self.payload,
            operation=self.operation,
            verbose=self.args.verbose)
        config.project = MavensMateProject(params=self.payload,ui=self.args.ui_switch)
        config.sfdc_client = config.project.sfdc_client

    def execute(self):
        """
            Executes requested command
        """
        try:
            self.__setup_connection()

            #if the arg switch argument is included, the request is to launch the out of box
            #MavensMate UI, so we generate the HTML for the UI and launch the process
            #example: mm -o new_project --ui
            if self.args.ui_switch == True:
                config.logger.debug('UI operation requested, attempting to launch MavensMate UI')
                tmp_html_file = util.generate_ui(self.operation,self.payload)
                util.launch_ui(tmp_html_file)
                self.__printr(util.generate_success_response('UI Generated Successfully'))
            
            #non-ui command
            else:        
                commands = get_available_commands()
                #debug(commands)
                try:
                    command_clazz = commands[self.operation](params=self.payload,args=self.args)                
                except KeyError:
                    raise MMUnsupportedOperationException('Could not find the operation you requested. Be sure the command is located in mm.commands, inherits from Command (found in basecommand.py) and includes an execute method.')
                except NotImplementedError:
                    raise MMException("This command is not properly implemented. Be sure it contains an 'execute' method.")
                self.__printr(command_clazz.execute())
        except Exception, e:
            self.__printr(e, is_exception=True)
    
    def __printr(self, response, is_exception=False):
        config.logger.debug('---------------------')
        config.logger.debug('result from command execution')
        config.logger.debug(response)
        config.logger.debug(type(response))
        config.logger.debug('---------------------')
        
        if type(response) is str or type(response) is unicode or is_exception:
            if self.response_format == "plain":
                if is_exception:
                    if hasattr(response, 'message'):
                        response = response.message
                    print response + "\n\n" + util.format_exception()
                else:
                    try:
                        obj = json.loads(response)
                        response = obj.get("body", "No response body included")
                    except ValueError:
                        pass #not valid json
                    print response
            elif self.response_format == "json":
                if is_exception:
                    #todo: move to generate method
                    if hasattr(response, 'message'):
                        json_res = {"body":response.message,"success":False,"stack_trace":util.format_exception()}
                    else:
                        json_res = {"body":str(response),"success":False,"stack_trace":util.format_exception()}
                    try:
                        response = json.dumps(json_res)
                        print response
                    except:
                        print json.dumps({"body":str(response),"success":False,"stack_trace":util.format_exception()})
                else:
                    try:
                        obj = json.loads(response)
                    except ValueError:
                        raise MMException("Response is not valid JSON")
                    print response
        elif type(response) is dict:
            if self.response_format == "plain":
                response = response.get("body", "No response body included")
                print response
            elif self.response_format == "json":
                response = json.dumps(response,indent=4)
                print response
        elif type(response) is list:
            if self.response_format == "plain":
                print response
            elif self.response_format == "json":
                response = json.dumps(response,indent=4)
                print response

        config.logger.debug('\n')
        config.logger.debug('---------------------')
        config.logger.debug('RESPONDING TO REQUEST')
        config.logger.debug('---------------------')
        config.logger.debug('\n')
        config.logger.debug(response)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--operation', help='The requested operation') #name of the operation being requested
    parser.add_argument('-c', '--client', help='The plugin client being used') #name of the plugin client ("SUBLIME_TEXT_2", "SUBLIME_TEXT_3", "TEXTMATE", "NOTEPAD_PLUS_PLUS", "BB_EDIT", etc.)
    parser.add_argument('-f', '--format', default='json', help='The response format') #json, plain
    parser.add_argument('--ui', action='store_true', default=False, 
        dest='ui_switch', help='Launch the default UI for the operation')
    parser.add_argument('--quiet', action='store_true', default=False, 
        dest='quiet', help='Suppresses mm.py output')
    parser.add_argument('--html', action='store_true', default=False, 
        dest='respond_with_html', help='Makes various commands return HTML')
    parser.add_argument('--v', '--verbose', action='store_true', default=False, 
        dest='verbose', help='Makes me really loud and annoying')
    args, unknown = parser.parse_known_args()
    return args, unknown

def get_request_payload():
    try:
        if sys.stdin.isatty():
            return {}
        return json.loads(sys.stdin.read())
    except ValueError:
        return {}

def get_available_commands():
    return lib.commands.command_list

def format_exception(exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()
    out = StringIO()
    traceback.print_exception(*exc_info, **dict(file=out))
    return out.getvalue()
