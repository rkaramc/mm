import os
import sys
import json
import subprocess
import lib.config as config
import lib.util as util
from lib.exceptions import *
from lib.basecommand import Command
from lib.project import MavensMateProject

debug = config.logger.debug

class NewProjectCommand(Command):
    """
        retrieves metadata from server, creates local project
    """
    def execute(self):
        debug('------> ')
        debug(self.params)
        try:
            if 'username' not in self.params or self.params['username'] == '':
                raise MMException('Please specify a username')
            if 'password' not in self.params or self.params['password'] == '':
                raise MMException('Please specify a password')
            if 'project_name' not in self.params or self.params['project_name'] == '':
                raise MMException('Please specify a project name')

            if ('action' in self.params and self.params['action'] == 'new') or 'action' not in self.params:
                if 'package' not in self.params or self.params['package'] == []:
                    self.params['package'] = {
                        'ApexClass'         : '*',
                        'ApexComponent'     : '*',
                        'ApexPage'          : '*',
                        'ApexTrigger'       : '*',
                        'StaticResource'    : '*'
                    }
                config.project = MavensMateProject(self.params)
                result = config.project.retrieve_and_write_to_disk()
            elif 'action' in self.params and self.params['action'] == 'existing':
                config.project = MavensMateProject(self.params)
                result = config.project.retrieve_and_write_to_disk('existing')

            if json.loads(result)['success'] == True and config.connection.get_plugin_client_setting('mm_open_project_on_create', True):
                #opens project based on the client
                client_location = config.connection.get_plugin_client_setting('mm_plugin_client_location')
                plugin_app_name = config.connection.get_plugin_client_setting('mm_osx_plugin_client_app_name') 
                if client_location == None:
                    client_location = '/Applications'
                if plugin_app_name == None:
                    plugin_app_name = 'Sublime Text 3.app'
                if config.connection.plugin_client == config.connection.PluginClients.SUBLIME_TEXT_2:
                    if sys.platform == 'darwin':
                        os.system("'{0}/Sublime Text 2.app/Contents/SharedSupport/bin/subl' --project '{1}'".format(client_location,config.project.location+"/"+config.project.project_name+".sublime-project"))
                elif config.connection.plugin_client == config.connection.PluginClients.SUBLIME_TEXT_3:
                    if sys.platform == 'darwin':
                        if os.path.exists(os.path.join('{0}/{1}'.format(client_location, plugin_app_name))):
                            os.system("'{0}/{1}/Contents/SharedSupport/bin/subl' --project '{2}'".format(client_location,plugin_app_name,config.project.location+"/"+config.project.project_name+".sublime-project"))
                        elif os.path.exists(os.path.join('{0}/Sublime Text 3.app'.format(client_location))):
                            os.system("'{0}/Sublime Text 3.app/Contents/SharedSupport/bin/subl' --project '{1}'".format(client_location,config.project.location+"/"+config.project.project_name+".sublime-project"))
                        else:
                            os.system("'{0}/Sublime Text.app/Contents/SharedSupport/bin/subl' --project '{1}'".format(client_location,config.project.location+"/"+config.project.project_name+".sublime-project"))
                    elif 'linux' in sys.platform:
                        subl_location = config.connection.get_plugin_client_setting('mm_subl_location', '/usr/local/bin/subl')
                        os.system("'{0}' --project '{1}'".format(subl_location,os.path.join(config.project.location,config.project.project_name+".sublime-project")))
                    else:
                        subl_location = config.connection.get_plugin_client_setting('mm_windows_subl_location')
                        if not os.path.isfile(subl_location) and "x86" not in subl_location:
                            subl_location = subl_location.replace("Program Files", "Program Files (x86)")
                        cmd = '"{0}" --project "{1}"'.format(subl_location,os.path.join(config.project.location,config.project.project_name+".sublime-project"))
                        subprocess.call(cmd)
            return result
        except BaseException, e:
            return util.generate_error_response(e.message)

class EditProjectCommand(Command):
    """
        edits the contents of the project based on a package definition
    """
    def execute(self):
        if 'package' not in self.params:
            raise MMException('"package" definition required in JSON body')
        package = self.params['package']

        #intercept and overwrite customobject retrieve to include standard objects
        if 'CustomObject' in package:
            for member in package['CustomObject']:
                if member == "*":
                    pass
                    #TODO

        clean_result = json.loads(config.project.clean(package=package,overwrite_package_xml=True))
        if clean_result['success'] == True:
            return util.generate_success_response('Project Edited Successfully')
        else:
            return util.generate_error_response(clean_result['body'])

class CleanProjectCommand(Command):
    """
        reverts a project to the server state based on the existing package.xml

        TODO: if the clean fails, we need to have a way to ensure the project is returned to its original state
        maybe we copy the project tree to a tmp folder, if we encounter an exception, we can remove the project
        and replace it with the copied one in tmp
        raise e
    """
    def execute(self):
        return config.project.clean()

class CompileProjectCommand(Command):
    """
        compiles the entire project
    """
    def execute(self):
        return config.project.compile(self.params)

class UpdateSubscriptionCommand(Command):
    def execute(self):
        return config.project.update_subscription(self.params)

class ProjectHealthCheckCommand(Command):
    def execute(self):
        return config.project.run_health_check()

class UpdateCredentialsCommand(Command):
    def execute(self):
        config.project.username = self.params['username']
        config.project.password = self.params['password']
        config.project.org_type = self.params['org_type']
        config.project.org_url  = self.params.get('org_url', None)
        config.project.update_credentials()
        return util.generate_success_response('Your credentials were updated successfully')
              
class UpgradeProjectCommand(Command):
    def execute(self):
        return config.project.upgrade()

class NewProjectFromExistingDirectoryCommand(Command):
    def execute(self):
        self.params["action"] = "existing"
        return NewProjectCommand(params=self.params).execute()
