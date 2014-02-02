import sys
import json
import os
import mm.util as util
import mm.xmltodict as xmltodict
import mm.config as config
import shutil
import urllib
import re
import threading
from operator import itemgetter
from xml.dom import minidom
import webbrowser
from mm.sfdc_client import MavensMateClient
from mm.exceptions import *
from mm.basecommand import Command

class NewMetadataCommand(Command):
    """
        Creates a new element of metadata
    """
    def execute(self):
        project = config.project
        sfdc_client = config.sfdc_client

        metadata_type                   = self.params.get('metadata_type', None)
        api_name                        = self.params.get('api_name', None)
        apex_class_type                 = self.params.get('apex_class_type', None)
        apex_trigger_object_api_name    = self.params.get('apex_trigger_object_api_name', None)
        apex_trigger_object_api_name    = self.params.get('apex_trigger_object_api_name', None)
        github_template                 = self.params.get('github_template', None)

        if metadata_type == 'ApexClass' and apex_class_type == None:
            apex_class_type = 'default'

        if api_name == None:
            return util.generate_error_response("You must provide a name for the new metadata.")

        #debug(type(api_name))

        if sfdc_client.does_metadata_exist(object_type=metadata_type, name=api_name) == True:
            mt = util.get_meta_type_by_name(metadata_type)
            filepath = os.path.join(project.location, 'src', mt['directoryName'], api_name+'.'+mt['suffix'])
            fetched = ""
            if not os.path.exists(filepath):
                self.params['files'] = [filepath]
                refresh_selected_metadata(self.params)
                fetched = ", fetched metadata file from server"
            raise MMException("This API name is already in use in your org" + fetched + ".")      

        tmp, tmp_unpackaged = util.put_tmp_directory_on_disk(True)
        
        util.put_skeleton_files_on_disk(metadata_type, api_name, tmp_unpackaged, apex_class_type, apex_trigger_object_api_name, github_template)
        package_xml_body = util.get_package_xml_contents({metadata_type : [ api_name ]})
        util.put_package_xml_in_directory(tmp_unpackaged, package_xml_body)
        zip_file = util.zip_directory(tmp, tmp)
        deploy_params = {
            "zip_file"          : zip_file,
            "rollback_on_error" : True,
            "ret_xml"           : True
        }
        deploy_result = sfdc_client.deploy(deploy_params)
        d = xmltodict.parse(deploy_result,postprocessor=util.xmltodict_postprocessor)
        meta_dir = ""
        files = []
        path = None
        for dirname, dirnames, filenames in os.walk(tmp_unpackaged):
            for filename in filenames:
                if 'package.xml' in filename:
                    continue
                full_file_path = os.path.join(dirname, filename)
                if '-meta.xml' in filename:
                    extension = filename.replace('-meta.xml','').split(".")[-1]
                else:
                    extension = filename.split(".")[-1]
                mt = util.get_meta_type_by_suffix(extension)
                if mt != None: 
                    meta_dir = mt['directoryName']
                    path = os.path.join(project.location, 'src', meta_dir)
                    if not os.path.exists(path):
                        os.makedirs(path)
                    files.append(os.path.join(path, filename))
                elif extension != "xml":
                    continue;
                # only apex files and meta.xml files should make it to here
                shutil.copy(full_file_path, path)
        shutil.rmtree(tmp)
        
        project.update_package_xml_with_metadata(metadata_type, api_name)
        project.conflict_manager.refresh_local_store(files=files)

        return json.dumps(d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result'])

class DeleteSelectedMetadataCommand(Command):
    aliases=["delete"]
    """
        Deletes metadata from the Salesforce.com server
    """
    def execute(self):
        project = config.project
        sfdc_client = config.sfdc_client
        files = self.params.get('files', None)
        for f in files:
            if '-meta.xml' in f:
                corresponding_file = f.split('-meta.xml')[0]
                if corresponding_file not in files:
                    files.append(corresponding_file)
        for f in files:
            if '-meta.xml' in f:
                continue
            file_ext = f.split('.')[-1]
            metadata_type = util.get_meta_type_by_suffix(file_ext)
            if metadata_type['metaFile'] == True:
                corresponding_file = f + '-meta.xml'
                if corresponding_file not in files:
                    files.append(corresponding_file)

        metadata_package_dict = util.get_metadata_hash(files)
        tmp, tmp_unpackaged = util.put_tmp_directory_on_disk(True)
        package_xml = util.get_package_xml_contents(metadata_package_dict)
        util.put_package_xml_in_directory(tmp_unpackaged, package_xml, True)
        empty_package_xml = util.get_empty_package_xml_contents()
        util.put_empty_package_xml_in_directory(tmp_unpackaged, empty_package_xml)
        zip_file = util.zip_directory(tmp, tmp)
        
        deploy_params = {
            "zip_file"          : zip_file,
            "rollback_on_error" : True,
            "ret_xml"           : True,
            "purge_on_delete"   : config.connection.get_plugin_client_setting("mm_purge_on_delete", False)
        }
        delete_result = sfdc_client.delete(deploy_params)
        d = xmltodict.parse(delete_result,postprocessor=util.xmltodict_postprocessor)
        shutil.rmtree(tmp)
        result = d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']
        if result['success'] == True:
            removed = []
            for f in files:
                try:
                    file_ext = f.split('.')[-1]
                    metadata_type = util.get_meta_type_by_suffix(file_ext)
                    if metadata_type == None or not 'directoryName' in metadata_type:
                        continue;
                    directory = metadata_type['directoryName']
                    filepath = os.path.join(project.location, "src", directory, f)
                    metapath = os.path.join(project.location, "src", directory, f + '-meta.xml')
                    os.remove(filepath)
                    os.remove(metapath)
                    # remove the entry in file properties
                    project.conflict_manager.remove_from_local_store(f)
                    removed.append(f)
                except Exception, e:
                    print e.message
            return util.generate_success_response("Removed metadata files: " + (",".join(removed)))
        else:
            return json.dumps(result)

class RefreshSelectedMetadataCommand(Command):
    """
        Refreshes metadata from the Salesforce.com server
    """
    name="refresh"
    def execute(self):
        project = config.project
        if 'directories' in self.params and len(self.params['directories']) == 1 and os.path.basename(self.params['directories'][0]) == "src":
            return project.clean(reset_metadata_container=False)
        else:
            retrieve_result = project.get_retrieve_result(self.params)
            #take this opportunity to freshen the cache
            project.conflict_manager.refresh_local_store(retrieve_result.fileProperties)
            util.extract_base64_encoded_zip(retrieve_result.zipFile, project.location)

            #TODO: handle exception that could render the project unusable bc of lost files
            #replace project metadata with retrieved metadata
            for dirname, dirnames, filenames in os.walk(os.path.join(project.location,"unpackaged")):
                for filename in filenames:
                    full_file_path = os.path.join(dirname, filename)
                    if '/unpackaged/package.xml' in full_file_path or '\\unpackaged\\package.xml' in full_file_path:
                        continue
                    if 'win32' in sys.platform:
                        destination = full_file_path.replace('\\unpackaged\\', '\\src\\')
                    else:
                        destination = full_file_path.replace('/unpackaged/', '/src/')
                    destination_directory = os.path.dirname(destination)
                    if not os.path.exists(destination_directory):
                        os.makedirs(destination_directory)
                    shutil.move(full_file_path, destination)
            shutil.rmtree(os.path.join(project.location,"unpackaged"))
            if os.path.exists(os.path.join(project.location,"metadata.zip")):
                os.remove(os.path.join(project.location,"metadata.zip"))
            return util.generate_success_response("Refresh Completed Successfully")

class OpenSelectedMetadataCommand(Command):
    aliases=["open_sfdc_url"]
    """
        Open selected file in SFDC
    """
    def execute(self):
        project = config.project
        sfdc_client = config.sfdc_client
        if "files" in params:
            if "type" in params: 
                open_type = params.get("type", None) 
            else:
                open_type = "edit"
            files = params.get("files", None)
            if len(files) > 0:
                apex_file_properties = util.parse_json_from_file(os.path.join(project.location,"config",".local_store"))
                opened = []
                for fileabs in files:
                    basename = os.path.basename(fileabs)

                    if basename not in apex_file_properties: 
                        # make sure we have meta data and then get the object type
                        if os.path.isfile(fileabs+"-meta.xml"):
                            xmldoc = minidom.parse(fileabs+"-meta.xml")
                            root = xmldoc.firstChild
                            object_type = root.nodeName
                        else:
                            continue

                        object_id = sfdc_client.get_apex_entity_id_by_name(object_type=object_type, name=basename)
                        if not object_id: 
                            continue
                    else:
                        props = apex_file_properties[basename]
                        object_type = props['type']
                        object_id = props['id']

                    # only ApexClasses that are global and have webservice scope have WSDL files
                    if open_type == "wsdl":
                        if object_type != "ApexClass":
                            continue
                        with open(fileabs, 'r') as content_file:
                            content = content_file.read()
                            p = re.compile("global\s+(abstract\s+)?class\s", re.I + re.M)
                            if not p.search(content):
                                continue
                            p = re.compile("\swebservice\s", re.I + re.M)
                            if not p.search(content): 
                                continue

                    # get the server instance url and set the redirect url
                    frontdoor = "https://" + sfdc_client.server_url.split('/')[2] + "/secur/frontdoor.jsp?sid=" + sfdc_client.sid + "&retURL="
                    if open_type == "wsdl":
                        f, e = os.path.splitext(basename)
                        ret_url = "/services/wsdl/class/" + f
                    else:
                        f, ext = os.path.splitext(basename)
                        if object_type == "CustomObject" and not f.endswith('__c'):
                            # standard object?
                            ret_url = "/p/setup/layout/LayoutFieldList?type=" + f + "%23CustomFieldRelatedList_target"                             
                        else:
                            ret_url = "/" + object_id

                    # open the browser window for this file and track it
                    webbrowser.open(frontdoor+ret_url, new=2)
                    opened.append(basename)
                if len(opened) == 0:
                    return util.generate_error_response("There were no valid files to open.")
                return util.generate_success_response("Opened "+(", ".join(opened))+" on server.")
            return util.generate_error_response("Unable to open file on server.")
        else:
            raise MMException("To open on Salesforce, you must provide an array of 'files'")

class CompileSelectedMetadataCommand(Command):
    """
        Compiles metadata
    """
    name="compile"
    def execute(self):        
        project = config.project

        files = self.params.get('files', None)
        use_tooling_api = config.connection.get_plugin_client_setting('mm_compile_with_tooling_api', False)
        check_for_conflicts = config.connection.get_plugin_client_setting('mm_compile_check_conflicts', False)

        compiling_apex_metadata = True
        for f in files:
            if f.split('.')[-1] not in util.TOOLING_API_EXTENSIONS:
                #cannot use tooling api
                compiling_apex_metadata = False
                break

        #when compiling apex metadata, check to see if it is newer on the server
        if check_for_conflicts and compiling_apex_metadata:
            if 'action' not in self.params or self.params['action'] != 'overwrite':
                has_conflict, msg = config.project.conflict_manager.check_for_conflicts(files)
                if has_conflict:
                    return msg
     
        #use tooling api here, if possible
        if use_tooling_api == True and compiling_apex_metadata and int(float(util.SFDC_API_VERSION)) >= 27:
            if 'metadata_container' not in project.settings or project.settings['metadata_container'] == None:
                container_id = project.sfdc_client.get_metadata_container_id()
                new_settings = project.settings
                new_settings['metadata_container'] = container_id
                project.__put_settings_file(new_settings)
            else:
                container_id = project.settings['metadata_container']
            
            file_ext = files[0].split('.')[-1]
            try:
                result = project.sfdc_client.compile_with_tooling_api(files, container_id)
            except MetadataContainerException as e:
                project.sfdc_client.delete_mavensmate_metadatacontainers_for_this_user()
                response = project.sfdc_client.new_metadatacontainer_for_this_user()
                project.__update_setting("metadata_container",response["id"])
                return project.compile_selected_metadata(self.params)

            if 'Id' in result and 'State' in result:
                if result['State'] == 'Completed':
                    project.conflict_manager.refresh_local_store(files=files)
                return util.generate_response(result)

        #the user has either chosen not to use the tooling api, or it's non apex metadata
        else:
            try:
                for f in files:
                    if '-meta.xml' in f:
                        corresponding_file = f.split('-meta.xml')[0]
                        if corresponding_file not in files:
                            files.append(corresponding_file)
                for f in files:
                    if '-meta.xml' in f:
                        continue
                    file_ext = f.split('.')[-1]
                    metadata_type = util.get_meta_type_by_suffix(file_ext)
                    if metadata_type == None:
                        if sys.platform == "win32":
                            dir_parts = f.split("\\")
                        else:
                            dir_parts = f.split("/")
                        if 'documents' in dir_parts:
                            metadata_type = util.get_meta_type_by_name("Document") 
                    if metadata_type != None and 'metaFile' in metadata_type and metadata_type['metaFile'] == True:
                        corresponding_file = f + '-meta.xml'
                        if corresponding_file not in files:
                            files.append(corresponding_file)

                metadata_package_dict = util.get_metadata_hash(files)
                #debug(metadata_package_dict)
                tmp = util.put_tmp_directory_on_disk()
                os.makedirs(os.path.join(tmp,"unpackaged"))
                #copy files from project directory to tmp
                for full_file_path in files:
                    if 'package.xml' in full_file_path:
                        continue
                    if config.is_windows: 
                        destination = os.path.join(tmp,'unpackaged',full_file_path.split('\src\\')[1])
                    else:
                        destination = os.path.join(tmp,'unpackaged',full_file_path.split('/src/')[1])
                    destination_directory = os.path.dirname(destination)
                    if not os.path.exists(destination_directory):
                        os.makedirs(destination_directory)
                    shutil.copy2(full_file_path, destination_directory)

                package_xml = util.get_package_xml_contents(metadata_package_dict)
                util.put_package_xml_in_directory(os.path.join(tmp,"unpackaged"), package_xml)
                zip_file = util.zip_directory(tmp, tmp)
                deploy_params = {
                    "zip_file"          : zip_file,
                    "rollback_on_error" : True,
                    "ret_xml"           : True
                }
                deploy_result = project.sfdc_client.deploy(deploy_params)

                d = xmltodict.parse(deploy_result,postprocessor=util.xmltodict_postprocessor)
                result = d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']
                shutil.rmtree(tmp)

                # Get new properties for the files we just compiled
                if result['success'] == True:
                    project.conflict_manager.refresh_local_store(files=files)

                return json.dumps(result)

            except Exception, e:
                try:
                    shutil.rmtree(tmp)
                except:
                    pass
                return util.generate_error_response(e.message)

class ListMetadataCommand(Command):
    def execute(self):
        if 'sid' in self.params:
            client = MavensMateClient(credentials={
                "sid"                   : self.params.get('sid', None),
                "metadata_server_url"   : urllib.unquote(self.params.get('metadata_server_url', None)),
                "server_url"            : urllib.unquote(self.params.get('server_url', None)),
            }) 
        elif 'username' in self.params:
            client = MavensMateClient(credentials={
                "username"              : self.params.get('username', None),
                "password"              : self.params.get('password', None),
                "org_type"              : self.params.get('org_type', None),
                "org_url"               : self.params.get('org_url', None)
            })
        return json.dumps(client.list_metadata(self.params['metadata_type']))

class RefreshMetadataIndexCommand(Command):
    def execute(self):
        IndexMetadataCommand(params=self.params).execute()
        return util.generate_success_response("Metadata refreshed successfully.")

class GetMetadataIndexCommand(Command):
    aliases=["get_indexed_metadata"]
    """
        Called by the MavensMate edit project dialog to display org metadata in tree
    """
    def execute(self):
        if 'keyword' in self.params or 'ids' in self.params:
            return config.project.filter_indexed_metadata(self.params)
        elif 'package_name' in self.params:
            return get_org_metadata(True, True, package_name=self.params["package_name"])
        else:
            return get_org_metadata(True, True)

def get_org_metadata(raw=False, selectBasedOnPackageXml=False, selectedIds=[], keyword=None, **kwargs):
    project = config.project
    if project.get_is_metadata_indexed():
        if raw:
            org_metadata_raw = util.get_file_as_string(os.path.join(project.location,"config",".org_metadata"))
            org_index = json.loads(org_metadata_raw)
            if selectBasedOnPackageXml:
                project.select_metadata_based_on_package_xml(org_index)
            elif len(selectedIds) > 0 or keyword != None:
                if keyword != None:
                    crawlJson.setVisibility(org_index, keyword)
                if len(selectedIds) > 0:
                    crawlJson.setChecked(org_index, selectedIds)
            return json.dumps(org_index)
        else:
            org_index = util.parse_json_from_file(os.path.join(project.location,"config",".org_metadata"))
            if selectBasedOnPackageXml:
                project.select_metadata_based_on_package_xml(org_index)
            elif len(selectedIds) > 0 or keyword != None:
                if keyword != None:
                    crawlJson.setVisibility(org_index, keyword)
                if len(selectedIds) > 0:
                    crawlJson.setChecked(org_index, selectedIds)
            return org_index
    else:
        index_metadata()
        org_index = util.parse_json_from_file(os.path.join(project.location,"config",".org_metadata"))
        project.select_metadata_based_on_package_xml(org_index)
        return org_index

class IndexMetadataCommand(Command):
    """
        compiles a list of all metadata in the org and places in .org_metadata file
    """
    def execute(self):
        mtypes = self.params.get('mtypes', None)
        project = config.project
        sfdc_client = config.sfdc_client
        return_list = []
        if sfdc_client == None or sfdc_client.is_connection_alive() == False:
            sfdc_client = MavensMateClient(credentials=project.get_creds(), override_session=True)  
            project.__set_sfdc_session()

        data = project.get_org_describe()
        threads = []
        thread_results = []
        creds = project.get_creds()

        to_be_indexed = []

        if mtypes != None:
            if type(mtypes) is not list:
                mtypes = [mtypes]
            for mt in mtypes:
                for md in data:
                    if md['xmlName'] == mt:
                        to_be_indexed.append(md)
                        break
        else:
            to_be_indexed = data

        metadata_chunks = list(util.grouper(8, to_be_indexed))
        for chunk in metadata_chunks:                    
            thread_client = MavensMateClient(credentials=creds)
            thread = IndexCall(thread_client, chunk)
            threads.append(thread)
            thread.start()
            
        for thread in threads:
            thread.join()
            if len(thread.results) == len(thread.clean_types):
                thread_results.extend(thread.results)
        
        return_list = sorted(thread_results, key=itemgetter('text')) 

        #no specific metadata types were requested, 
        #so we simply overwirte .org_metadata with the new index 
        if mtypes == None:
            file_body = json.dumps(return_list, sort_keys=False, indent=4)
            src = open(os.path.join(project.location,"config",".org_metadata"), "w")
            src.write(file_body)
            src.close()
            #return file_body
        #specific metadata types were requested, so update .org_metadata with the result
        elif type(return_list) is list and len(return_list) > 0:
            existing_index = project.get_org_metadata()
            for mt in return_list:
                for emt in existing_index:
                    if emt['xmlName'] == mt['xmlName']:
                        emt['children'] = mt['children']
                        break

            file_body = json.dumps(existing_index, sort_keys=False, indent=4)
            src = open(os.path.join(project.location,"config",".org_metadata"), "w")
            src.write(file_body)
            src.close()
            #return file_body
        return util.generate_success_response("Org indexed successfully")

class IndexCall(threading.Thread):
    def __init__(self, client, metadata_types):
        self.metadata_types = metadata_types
        self.client         = client
        self.results        = []
        self.clean_types    = []
        for mt in self.metadata_types:
            if mt != None:
                self.clean_types.append(mt)
        threading.Thread.__init__(self)

    def run(self):
        for mtype in self.clean_types:
            if mtype == None:
                self.results.append({})
                continue
            try:
                result = self.client.list_metadata(mtype['xmlName'])
                if result == None:
                    result = []
                self.results.append({
                    "title"         : mtype['xmlName'],
                    "text"          : mtype['xmlName'],
                    "xmlName"       : mtype['xmlName'],
                    "type"          : mtype,
                    "cls"           : "folder",
                    "expanded"      : False,
                    "children"      : result,
                    "checked"       : False,
                    "select"        : False,
                    "level"         : 1,
                    "id"            : mtype['xmlName'],
                    "key"           : mtype['xmlName'],
                    "isFolder"      : True,
                    "cls"           : "folder",
                    "inFolder"      : mtype['inFolder'],
                    "hasChildTypes" : 'childXmlNames' in mtype

                })
            except:
                self.results.append({
                    "title"         : mtype['xmlName'], 
                    "text"          : mtype['xmlName'],
                    "xmlName"       : mtype['xmlName'],
                    "type"          : mtype,
                    "cls"           : "folder",
                    "expanded"      : False,
                    "children"      : [],
                    "checked"       : False,
                    "select"        : False,
                    "level"         : 1,
                    "id"            : mtype['xmlName'],
                    "key"           : mtype['xmlName'],
                    "isFolder"      : True,
                    "cls"           : "folder",
                    "inFolder"      : mtype['inFolder'],
                    "hasChildTypes" : 'childXmlNames' in mtype
                })
                continue