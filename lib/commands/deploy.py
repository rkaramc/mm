import os
import time
import threading
import shutil
import lib.util as util
import lib.config as config
import datetime
import sys
import json
from lib.sfdc_client import MavensMateClient
from lib.exceptions import *
from lib.basecommand import Command

debug = config.logger.debug

class DeloyToServerCommand(Command):
    name="deploy"
    aliases=["deploy_to_server"]
    """
        Deploys metadata to one or more orgs
    """
    def execute(self):
        archive_deployments = config.connection.get_plugin_client_setting("mm_archive_deployments", True)
        finish_deploy = self.params.get('finish', False)
        compare = config.connection.get_plugin_client_setting("mm_compare_before_deployment", True)
        destinations = self.params['destinations']
        deploy_metadata = config.sfdc_client.retrieve(package=self.params['package'])
        deploy_name = self.params.get('new_deployment_name', None)
        threads = []
        
        if not finish_deploy and compare:
            source_retrieve_result = config.sfdc_client.retrieve(package=self.params['package'])
            debug('source_retrieve_result')
            debug(source_retrieve_result)

            source_dict = {}
            for fp in source_retrieve_result.fileProperties:
                source_dict[fp.fileName] = fp

            debug('source_dict')
            debug(source_dict) 

            #need to compare package.xml to destination orgs here
            for destination in destinations:
                thread = CompareHandler(config.project, destination, self.params, self.params['package'])
                threads.append(thread)
                thread.start()  
                
            compare_results = []
            for thread in threads:
                thread.join()  
                compare_results.append(thread.result)
            
            debug('compare_results')
            debug(compare_results)
            destination_dict = {}

            for cr in compare_results:
                cr_dict = {}
                for fpfp in cr.fileProperties:
                    cr_dict[fpfp.fileName] = fpfp
                destination_dict[cr.username] = cr_dict

            debug('destination_dict')
            debug(destination_dict)    

            final_compare_result = {}
            for d in destinations:
                final_compare_result[d['username']] = {}

            for file_name, file_details in source_dict.iteritems():
                if 'package.xml' in file_name:
                    continue; 
                for username, username_value in destination_dict.iteritems():
                    destination_retrieve_details = destination_dict[username]
                    
                    if 'package.xml' in file_name:
                        continue

                    short_file_name = file_name.split('/')[-1]
                    mtype = util.get_meta_type_by_suffix(short_file_name.split('.')[-1])
   
                    if file_name not in destination_retrieve_details:
                        final_compare_result[username][file_name] = {
                            'name' : short_file_name,
                            'type' : mtype['xmlName'],
                            'action': 'insert',
                            'message' : 'Create'
                        }
                    else:
                        destination_file_detail = destination_retrieve_details[file_name]
                        source_file_detail = source_dict[file_name]
                        if source_file_detail.lastModifiedDate >= destination_file_detail.lastModifiedDate:
                            final_compare_result[username][file_name] = {
                                'name' : short_file_name,
                                'type' : mtype['xmlName'],
                                'action' : 'update',
                                'message' : 'You will overwrite this file'
                            }
                        else:
                            final_compare_result[username][file_name] = {
                                'name' : short_file_name,
                                'type' : mtype['xmlName'],
                                'action' : 'update_conflict',
                                'message' : 'Destination file is newer than source file'
                            }
            


            # final_compare_result = {}
            # for d in destinations:
            #     final_compare_result[d['username']] = {}

            # for username, username_value in destination_dict.iteritems():
            #     #destination_dict = destination_dict[username]
            #     for file_name, file_details in username_value.iteritems():
            #         if 'package.xml' in file_name:
            #             continue;

            #         short_file_name = file_name.split('/')[-1]
            #         mtype = util.get_meta_type_by_suffix(short_file_name.split('.')[-1])

            #         if file_name not in source_dict:
            #             final_compare_result[username][file_name] = {
            #                 'name' : short_file_name,
            #                 'type' : mtype['xmlName'],
            #                 'action': 'insert',
            #                 'message' : 'Create'
            #             }
            #         else:
            #             destination_file_detail = username_value[file_name]
            #             source_file_detail = source_dict[file_name]
            #             if source_file_detail.lastModifiedDate >= destination_file_detail.lastModifiedDate:
            #                 final_compare_result[username][file_name] = {
            #                     'name' : short_file_name,
            #                     'type' : mtype['xmlName'],
            #                     'action' : 'update',
            #                     'message' : 'You will overwrite this file'
            #                 }
            #             else:
            #                 final_compare_result[username][file_name] = {
            #                     'name' : short_file_name,
            #                     'type' : mtype['xmlName'],
            #                     'action' : 'update_conflict',
            #                     'message' : 'Destination file is newer than source file'
            #                 }

            debug('final_compare_result')
            debug(final_compare_result) 

            if self.args.respond_with_html == True:
                html = util.generate_html_response('deploy_compare', final_compare_result, self.params)
                response = json.loads(util.generate_success_response(html, "html"))
                response['compare_success'] = True
                # if deployment to one org fails, the entire deploy was not successful
                # for result in final_compare_result:
                #     if result['success'] == False:
                #         response['compare_success'] = False
                #         break
                return json.dumps(response)
            else:
                return json.dumps(final_compare_result,index=4)   

        for destination in destinations:
            if archive_deployments:
                deploy_path = os.path.join(config.project.location,"deploy",destination['username'])
                if not os.path.exists(deploy_path):
                    os.makedirs(deploy_path)
                if not os.path.isfile(os.path.join(config.project.location,"deploy",'.config')):
                    config_file = open(os.path.join(config.project.location,"deploy",'.config'), 'wb')
                    config_file_contents = { 
                        'deployments' : {
                            'named' : [],
                            'timestamped' : []
                        }
                    }
                    config_file.write(json.dumps(config_file_contents))
                    config_file.close()   

                ts = time.time()
                if not config.is_windows:
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H %M %S')

                if deploy_name:
                    if os.path.isdir(os.path.join(config.project.location,"deploy",destination['username'],deploy_name)):
                        shutil.rmtree(os.path.join(config.project.location,"deploy",destination['username'],deploy_name))
                    os.makedirs(os.path.join(config.project.location,"deploy",destination['username'],deploy_name))
                    util.extract_base64_encoded_zip(deploy_metadata.zipFile, os.path.join(config.project.location,"deploy",destination['username'],deploy_name))

                    config_file_json = util.parse_json_from_file(os.path.join(config.project.location,"deploy",'.config'))
                    named_deployment = {
                        'destination' : destination['username'],
                        'name' : deploy_name,
                        'timestamp' : timestamp,
                        'id' : util.get_random_string(30),
                        'package' : os.path.join(config.project.location,"deploy",destination['username'],deploy_name,'unpackaged','package.xml')
                    }
                    config_file_json['deployments']['named'].append(named_deployment)
                    config_file = open(os.path.join(config.project.location,"deploy",'.config'), 'wb')
                    config_file.write(json.dumps(config_file_json))
                    config_file.close()
                else:
                    os.makedirs(os.path.join(config.project.location,"deploy",destination['username'],timestamp))
                    util.extract_base64_encoded_zip(deploy_metadata.zipFile, os.path.join(config.project.location,"deploy",destination['username'],timestamp))

                    config_file_json = util.parse_json_from_file(os.path.join(config.project.location,"deploy",'.config'))
                    timestamped_deployment = {
                        'destination' : destination['username'],
                        'timestamp' : timestamp,
                        'id' : util.get_random_string(30),
                        'package' : os.path.join(config.project.location,"deploy",destination['username'],timestamp,'unpackaged','package.xml')
                    }
                    config_file_json['deployments']['timestamped'].append(timestamped_deployment)
                    config_file = open(os.path.join(config.project.location,"deploy",'.config'), 'wb')
                    config_file.write(json.dumps(config_file_json))
                    config_file.close()

            thread = DeploymentHandler(config.project, destination, self.params, deploy_metadata)
            threads.append(thread)
            thread.start()  
        deploy_results = []
        for thread in threads:
            thread.join()  
            deploy_results.append(thread.result)
                
        if self.args.respond_with_html == True:
            html = util.generate_html_response(self.args.operation, deploy_results, self.params)
            response = json.loads(util.generate_success_response(html, "html"))
            response['deploy_success'] = True
            # if deployment to one org fails, the entire deploy was not successful
            for result in deploy_results:
                if result['success'] == False:
                    response['deploy_success'] = False
                    break
            return json.dumps(response)
        else:
            return json.dumps(deploy_results,index=4)

class GetOrgConnectionsCommand(Command):
    """
        returns a list of all org connections for this config.project
    """
    name="get_org_connections"
    aliases=["list_connections"]
    def execute(self):
        return config.project.get_org_connections()
        
class NewOrgConnectionCommand(Command):
    aliases=["new_connection"]
    """
        creates a new org connection
    """
    def execute(self):
        c = MavensMateClient(credentials={
            "username"  :   self.params['username'],
            "password"  :   self.params['password'],
            "org_type"  :   self.params['org_type']
        })
        org_connection_id = util.new_mavensmate_id()
        util.put_password_by_key(org_connection_id, self.params['password'])
        org_connections = GetOrgConnectionsCommand(params=self.params).execute()
        org_connections.append({
            'id'            : org_connection_id,
            'username'      : self.params['username'],
            'environment'   : self.params['org_type']
        })
        src = open(os.path.join(config.project.location,"config",".org_connections"), 'wb')
        json_data = json.dumps(org_connections, sort_keys=False, indent=4)
        src.write(json_data)
        src.close()
        return util.generate_success_response('Org Connection Successfully Created')

class GetDeploymentNamesCommand(Command):
    """
        returns a list of all org connections for this config.project
    """
    def execute(self):
        package_names = ["package.xml"]
        try:
            if not os.path.exists(os.path.join(config.project.location,"deploy")):
                return package_names
            else:
                for dirname, dirnames, filenames in os.walk(os.path.join(config.project.location,"deploy")):
                    for filename in filenames:
                        if filename == "package.xml":
                            full_file_path = os.path.join(dirname, filename)
                            if "linux" in sys.platform or "darwin" in sys.platform:
                                directory_parts = full_file_path.split("/");
                            else:
                                directory_parts = full_file_path.split("\\");
                            directory_parts.remove("package.xml")
                            directory_parts.remove("unpackaged")
                            package_names.append(" | ".join(directory_parts[-2:]))
        except:
            return package_names
        return package_names

class DeleteOrgConnectionCommand(Command):
    aliases=["delete_connection"]
    """
        delete a specific org connection
    """
    def execute(self):  
        org_connections = GetOrgConnectionsCommand(params=self.params).execute()
        config.logger.debug('=======')
        config.logger.debug(org_connections)
        updated_org_connections = []
        for connection in org_connections:
            if connection['id'] != self.params['id']:
                updated_org_connections.append(connection)
        src = open(os.path.join(config.project.location,"config",".org_connections"), 'wb')
        json_data = json.dumps(updated_org_connections, sort_keys=False, indent=4)
        src.write(json_data)
        src.close()
        util.delete_password_by_key(self.params['id'])
        return util.generate_success_response('Org Connection Successfully Deleted')

class CompareHandler(threading.Thread):
    def __init__(self, project, destination, params, package):
        self.project            = project
        self.destination        = destination
        self.params             = params
        self.package            = package #location of package.xml
        self.result             = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            if 'password' not in self.destination:
                self.destination['password'] = util.get_password_by_key(self.destination['id'])
            deploy_client = MavensMateClient(credentials={
                "username":self.destination['username'],
                "password":self.destination['password'],
                "org_type":self.destination['org_type']
            })    

            retrieve_result = deploy_client.retrieve(package=self.package)
            retrieve_result['username'] = self.destination['username']
            debug('>>>>>> RETRIEVE RESULT >>>>>>')
            debug(retrieve_result)
            self.result = retrieve_result
        except BaseException, e:
            result = util.generate_error_response(e.message, False)
            result['username'] = self.destination['username']
            self.result = result

class DeploymentHandler(threading.Thread):

    def __init__(self, project, destination, params, deploy_metadata):
        self.project            = project
        self.destination        = destination
        self.params             = params
        self.deploy_metadata    = deploy_metadata
        self.result             = None
        threading.Thread.__init__(self)

    def run(self):
        try:
            if 'password' not in self.destination:
                self.destination['password'] = util.get_password_by_key(self.destination['id'])
            deploy_client = MavensMateClient(credentials={
                "username":self.destination['username'],
                "password":self.destination['password'],
                "org_type":self.destination['org_type']
            })    

            # Check testRequired to find out if this is a production org.
            # This is a bit of a misnomer as runAllTests=True will run managed package tests, other 
            # tests are *always* run so we should honor the UI, however Production orgs do require 
            # rollbackOnError=True so we should override it here
            describe_result = deploy_client.describeMetadata(retXml=False)
            if describe_result.testRequired == True:
                self.params['rollback_on_error'] = True

            self.params['zip_file'] = self.deploy_metadata.zipFile      
            deploy_result = deploy_client.deploy(self.params)
            deploy_result['username'] = self.destination['username']
            debug('>>>>>> DEPLOY RESULT >>>>>>')
            debug(deploy_result)
            self.result = deploy_result
        except BaseException, e:
            result = util.generate_error_response(e.message, False)
            result['username'] = self.destination['username']
            self.result = result