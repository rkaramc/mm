import os.path
import util
import json
import config
import threading
from exceptions import MMException

debug = config.logger.debug

class ConflictManager(object):
    def __init__(self, project):
        self.project = project
        self.local_store_path = os.path.join(self.project.location,"config",".local_store")

    #creates a .local_store file with the retrieve result from the project, sets values to "clean"
    def init_local_store(self, retrieve_result):
        apex_file_properties = {}
        fileProperties = retrieve_result.fileProperties
        for prop in fileProperties:
            if prop.type != "Package":
                filename = prop.fileName.split('/')[-1];
                fileprop = {
                    'createdById': prop.createdById,
                    'createdByName': prop.createdByName,
                    'createdDate': str(prop.createdDate),
                    'fileName': prop.fileName,
                    'fullName': prop.fullName,
                    'id': prop.id,
                    'lastModifiedById': prop.lastModifiedById,
                    'lastModifiedByName': prop.lastModifiedByName,
                    'lastModifiedDate': str(prop.lastModifiedDate),
                    'type': prop.type
                }
                fileprop['mmState'] = 'clean'
                apex_file_properties[filename] = fileprop
        self.write_local_store(apex_file_properties)

    def get_retrieve_result(self, params):
        if 'directories' in params and len(params['directories']) > 0 and 'files' in params and len(params['files']) > 0:
            raise MMException("Please select either directories or files to refresh, not both")
        elif 'directories' in params and len(params['directories']) > 0:
            metadata = {}
            types = []
            for d in params['directories']:
                basename = os.path.basename(d)
                # refresh all if it's the project base or src directory
                if basename == config.project.project_name or basename == "src":
                    data = util.get_default_metadata_data();
                    if type(data) is dict and 'metadataObjects' in data:
                        data = data['metadataObjects']
                    for item in data: 
                        if 'directoryName' in item:
                            types.append(item['xmlName'])
                else:
                    metadata_type = util.get_meta_type_by_dir(basename)
                    if metadata_type:
                        types.append(metadata_type['xmlName'])
                        if 'childXmlNames' in metadata_type:
                            for child in metadata_type['childXmlNames']:
                                types.append(child)
          
            custom_fields = []
            for val in self.project.get_package_types():
                package_type = val['name']
                members = val['members']
                if package_type not in types:
                    continue;

                metadata[package_type] = members

                if package_type == 'CustomObject':
                    for member in members:
                        if members == "*":
                            for item in self.project.get_org_metadata():
                               if item['xmlName'] == 'CustomObject':
                                    for child in item['children']:
                                        if not child['title'].endswith("__c"):
                                            for props in child['children']:
                                                if props['title'] == 'fields':
                                                    for field in props['children']:
                                                        custom_fields.append(child['title']+'.'+field['title'])
                                                    break
                                            if member != "*":
                                                break
                                    break

                    if len(custom_fields):
                        if 'CustomField' not in metadata:
                            metadata['CustomField'] = []
                        metadata['CustomField'] = list(set(metadata['CustomField']+custom_fields))

            if len(metadata) == 0:
                raise MMException("Could not find metadata types to refresh")
        elif 'files' in params and len(params['files']) > 0:
            metadata = util.get_metadata_hash(params['files'])
        else:
            raise MMException("Please provide either an array of 'directories' or an array of 'files'")

        #retrieves a fresh set of metadata based on the files that have been requested
        retrieve_result = self.project.sfdc_client.retrieve(package=metadata)
        return retrieve_result  

    def check_for_conflicts(self, files):
        local_store = self.get_local_store()
        retrieve_result = self.project.get_retrieve_result({"files":files})
        properties = retrieve_result.fileProperties
        for f in files:
            ext = util.get_file_extension_no_period(f)
            apex_type = util.get_meta_type_by_suffix(ext)
            apex_entity_api_name = util.get_file_name_no_extension(f)
            body_field = 'Body'
            if apex_type['xmlName'] == 'ApexPage' or apex_type['xmlName'] == 'ApexComponent':
                body_field = 'Markup'
            api_name_plus_extension = apex_entity_api_name+"."+ext
            
            server_property = None
            for p in properties:
                if p["fullName"] == apex_entity_api_name:
                    server_property = p
                    try:
                        config.api_name_to_id_dict[p["fullName"]] = p["id"]
                    except:
                        pass
                    break
            if api_name_plus_extension in local_store and server_property != None:
                local_store_entry = local_store[api_name_plus_extension]
                local_last_modified_date = local_store_entry["lastModifiedDate"]
                server_last_modified_date = server_property['lastModifiedDate']
                last_modified_name = server_property['lastModifiedByName']
                qr = self.project.sfdc_client.query("Select LastModifiedById, LastModifiedDate, LastModifiedBy.Name, {0} From {1} Where Name = '{2}'".format(body_field, apex_type['xmlName'], apex_entity_api_name))
                body = qr['records'][0][body_field]
                body = body.encode('utf-8')
                if str(local_last_modified_date) != str(server_last_modified_date) or local_store_entry['mmState'] == 'dirty':
                    if local_store_entry['mmState'] != 'dirty':
                        local_store_entry['mmState'] = 'dirty'
                    msg = util.generate_request_for_action_response(
                        "The local version of your file and the server copy are out of sync.\n\n{0} was last modified by {1} on {2}."
                        .format(apex_entity_api_name, last_modified_name, server_last_modified_date),
                        'compile',
                        ["Diff With Server","Operation Canceled"],
                        tmp_file_path=util.put_tmp_file_on_disk(apex_entity_api_name, body, apex_type.get('suffix', ''))
                    )
                    self.mark_dirty(api_name_plus_extension)
                    return True, msg
        return False, None

    def get_local_store(self):
        local_store = None
        try:
            local_store = util.parse_json_from_file(self.local_store_path)
        except:
            pass
        if local_store == None:
            local_store = {}
        return local_store

    def remove_from_local_store(self, api_name_plus_extension):
        local_store = self.get_local_store()
        local_store.pop(api_name_plus_extension, None)
        self.write_local_store(local_store)

    def mark_dirty(self, api_name):
        local_store = self.get_local_store()
        local_store[api_name]['mmState'] = 'dirty'
        self.write_local_store(local_store)

    def refresh_local_store_async(self, properties=None, **kwargs):
        if 'files' in kwargs:
            params = {"files":kwargs['files']}
            retrieve_result = self.get_retrieve_result(params)
            properties = retrieve_result.fileProperties
        elif 'directories' in kwargs:
            params = {"directories":kwargs['directories']}
            retrieve_result = self.get_retrieve_result(params)
            properties = retrieve_result.fileProperties

        if not len(properties):
            return;
        
        local_store = self.get_local_store()

        for prop in properties:
            if prop.type != "Package":
                
                #debug('>>>>>> ')
                #debug(prop.lastModifiedDate)
                #debug(str(prop.lastModifiedDate))

                filename = prop.fileName.split('/')[-1];
                fileprop = {
                    'createdById': prop.createdById,
                    'createdByName': prop.createdByName,
                    'createdDate': str(prop.createdDate),
                    'fileName': prop.fileName,
                    'fullName': prop.fullName,
                    'id': prop.id,
                    'lastModifiedById': prop.lastModifiedById,
                    'lastModifiedByName': prop.lastModifiedByName,
                    'lastModifiedDate': str(prop.lastModifiedDate),
                    'type': prop.type
                }
                fileprop['mmState'] = 'clean'
                local_store[filename] = fileprop
        self.write_local_store(local_store)

    def refresh_local_store(self, properties=None, **kwargs):
        t1 = threading.Thread(self.refresh_local_store_async(properties, **kwargs))
        t1.daemon = True
        t1.start()

    def write_local_store(self, json_data):
        src = open(self.local_store_path, "w")
        json_data = json.dumps(json_data, sort_keys=True, indent=4)
        src.write(json_data)
        src.close()