import sys
import json
import os
import util
import config
import xmltodict
import requests
import time
import urllib
import datetime
import re
from operator import itemgetter
sys.path.append('../')

from exceptions import *
from sforce.base import SforceBaseClient
from suds import WebFault
from sforce.partner import SforcePartnerClient
from sforce.metadata import SforceMetadataClient
from sforce.apex import SforceApexClient
from sforce.tooling import SforceToolingClient

debug = config.logger.debug

class MavensMateClient(object):

    def __init__(self, **kwargs):
        self.credentials            = kwargs.get('credentials', None)
        self.override_session       = kwargs.get('override_session', False)

        self.reset_creds            = False #set flag to true to have MavensMateProject restore creds

        self.username               = None
        self.password               = None
        self.sid                    = None
        self.user_id                = None
        self.server_url             = None
        self.metadata_server_url    = None
        self.endpoint               = None
        self.pod                    = None

        #salesforce connection bindings
        self.pclient                = None
        self.mclient                = None
        self.aclient                = None
        self.tclient                = None

        #print self.credentials

        if self.credentials != None:
            self.username               = self.credentials['username']              if 'username' in self.credentials else None
            self.password               = self.credentials['password']              if 'password' in self.credentials else None
            self.sid                    = self.credentials['sid']                   if 'sid' in self.credentials else None
            self.user_id                = self.credentials['user_id']               if 'user_id' in self.credentials else None
            self.metadata_server_url    = self.credentials['metadata_server_url']   if 'metadata_server_url' in self.credentials else None
            self.server_url             = self.credentials['server_url']            if 'server_url' in self.credentials else None
            self.org_type               = self.credentials['org_type']              if 'org_type' in self.credentials else 'production'
            
            if 'org_url' in self.credentials and self.credentials['org_url'] != None and self.credentials['org_url'] != '':
                self.endpoint = util.get_soap_url_from_custom_url(self.credentials["org_url"])
            elif self.override_session == False and 'endpoint' in self.credentials and self.credentials['endpoint'] != None:
                self.endpoint = self.credentials['endpoint']    
            else:
                self.endpoint = util.get_sfdc_endpoint_by_type(self.org_type) 

        #we do this to prevent an unnecessary "login" call
        #if the getUserInfo call fails, we catch it and reset our class variables 
        if self.override_session == False and self.sid != None and self.user_id != None and self.metadata_server_url != None and self.endpoint != None and self.server_url != None:
            self.pclient = self.__get_partner_client()
            self.pclient._setEndpoint(self.server_url)

            header = self.pclient.generateHeader('SessionHeader')
            header.sessionId = self.sid
            self.pclient.setSessionHeader(header)
            self.pclient._setHeaders('')

            result = None
            try:
                debug('GETTING USER INFO')
                result = self.pclient.getUserInfo()
                debug(result)
            except WebFault, e:
                debug(self.credentials)

                #exception here means most likely that cached auth creds are no longer valid
                #we're ok with this, the script will attempt another login
                self.sid = None
        elif self.server_url == None:
            self.pclient = self.__get_partner_client()
            self.login()
            self.reset_creds = True  

        #if the cached creds didnt work & username/password/endpoint are not provided, get them from keyring
        if self.sid == None or self.override_session == True:
            self.pclient = self.__get_partner_client()
            self.login()   
            self.reset_creds = True

    def login(self):
        result = None
        try:
            result = self.pclient.login(self.username, self.password, '')
        except WebFault, e:
            raise e
        config.logger.debug('LOGIN RESULT')
        config.logger.debug(result)
        self.metadata_server_url    = result.metadataServerUrl
        self.sid                    = result.sessionId
        self.user_id                = result.userId
        self.server_url             = result.serverUrl
        #TODO: do need to reset clients here now?

    def is_connection_alive(self):
        try:
            self.pclient.getUserInfo()
            debug("Cached connection still alive")
        except WebFault:
            debug("Cached connection dead")
            return False
        return True

    def compile_apex(self, type, body, **kwargs):
        ac = self.__get_apex_client()
        compile_result = None
        if type == 'class' or type == 'ApexClass':
            compile_result = ac.compileClasses(body, **kwargs)
        elif type == 'trigger' or type == 'ApexTrigger':
            compile_result = ac.compileTriggers(body, **kwargs)
        return compile_result

    def execute_apex(self, params):
        ac = self.__get_apex_client()
        execute_apex_result = ac.executeAnonymous(params)
        return execute_apex_result

    def describeMetadata(self, **kwargs):
        if self.mclient == None:
            self.mclient = self.__get_metadata_client()
        if config.describe_data == None:
            config.describe_data = self.mclient.describeMetadata(**kwargs)
        return config.describe_data

    def describeObject(self, object_name):
        r = requests.get(self.get_base_url()+"/sobjects/"+object_name+"/describe", headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            _exception_handler(r)
        r.raise_for_status()
        return r.text

    def get_org_metadata(self, as_dict=True, **kwargs):
        describe_result = self.describeMetadata()
        d = xmltodict.parse(describe_result,postprocessor=util.xmltodict_postprocessor)
        result = d["soapenv:Envelope"]["soapenv:Body"]["describeMetadataResponse"]["result"]
        mlist = []
        subscription_setting = kwargs.get('subscription', None)
        if subscription_setting == None:
            subscription_setting = config.connection.get_plugin_client_setting('mm_default_subscription')
        if subscription_setting != None and type(subscription_setting) is list:
            for m in result['metadataObjects']:
                if m['xmlName'] in subscription_setting:
                    mlist.append(m)
        sorted_list = sorted(mlist, key=itemgetter('xmlName'))
        if as_dict:
            return util.prepare_for_metadata_tree( sorted_list )
        else:
            return json.dumps(sorted_list, sort_keys=True, indent=4)

    def retrieve(self, **kwargs):
        if self.mclient == None:
            self.mclient = self.__get_metadata_client()
        return self.mclient.retrieve(**kwargs)

    def deploy(self, params, **kwargs):
        if self.mclient == None:
            self.mclient = self.__get_metadata_client()
        return self.mclient.deploy(params, **kwargs)

    def delete(self, params, **kwargs):
        if self.mclient == None:
            self.mclient = self.__get_metadata_client()
        return self.mclient.deploy(params, **kwargs)

    def list_metadata(self, metadata_type, simple=False):
        if self.mclient == None:
            self.mclient = self.__get_metadata_client()
        if simple:
            return self.mclient.listMetadata(metadata_type)
        else:
            return self.mclient.listMetadataAdvanced(metadata_type)

    def run_tests(self, params):
        if self.aclient == None:
            self.aclient = self.__get_apex_client()
        params['namespace'] = self.get_org_namespace()
        return self.aclient.runTests(params)

    def get_org_namespace(self):
        if self.mclient == None:
            self.mclient = self.__get_metadata_client()
        return self.mclient.getOrgNamespace() 

    def does_metadata_exist(self, **kwargs):
        if self.pclient == None:
            self.pclient = self.__get_partner_client()
        query_result = self.pclient.query('select count() From '+kwargs['object_type']+' Where Name = \''+kwargs['name']+'\' AND NamespacePrefix = \''+self.get_org_namespace()+'\'')
        return True if query_result.size > 0 else False

    def execute_query(self, soql):
        if self.pclient == None:
            self.pclient = self.__get_partner_client()
        query_result = self.pclient.query(soql)
        return query_result

    def get_apex_entity_id_by_name(self, **kwargs):
        if self.pclient == None:
            self.pclient = self.__get_partner_client()
        class_or_trigger_names = kwargs.get('class_or_trigger_names', None)
        object_type = kwargs.get('object_type', "ApexClass")
        if class_or_trigger_names == None:
            query_result = self.pclient.query('select Id, Name From '+kwargs['object_type']+' Where Name = \''+kwargs['name']+'\' AND NamespacePrefix = \''+self.get_org_namespace()+'\'')
            config.logger.debug(">>>>>> ",query_result)
            record_id = None
            try:
                record_id = query_result.records[0].Id
            except:
                pass
            return record_id
        else:
            name_string = "','".join(class_or_trigger_names)
            name_string = "'"+name_string+"'"
            query_result = self.pclient.query("select Id, Name From {0} Where Name IN ({1}) AND NamespacePrefix = '{2}'".format(object_type, name_string, self.get_org_namespace()))
            try:
                return query_result.records
            except:
                pass
            return []

    def get_apex_classes_and_triggers(self, **kwargs):
        return_list = {
            "Apex Classes" : [],
            "Apex Triggers" : []
        }
        if self.pclient == None:
            self.pclient = self.__get_partner_client()
        query_result = self.pclient.query('SELECT Id, Name From ApexClass Where NamespacePrefix = null Order By Name')
        try:
            recs = query_result['records']
            for a in recs:
                return_list["Apex Classes"].append(a)
        except:
            pass
        query_result = self.pclient.query('SELECT Id, Name From ApexTrigger Where NamespacePrefix = null AND Status = \'Active\' Order By Name')
        try:
            recs = query_result['records']
            for a in recs:
                return_list["Apex Triggers"].append(a)
        except:
            pass
        return return_list

    ##TOOLING API PLUMMING##
    ##TODO: MOVE TO A MODULE##

    #compiles files with the tooling api
    #if multiple files are sent, we need to create
    #"members" for all of them associated to a single
    #metadatacontainerid and send that container for compile
    def compile_with_tooling_api(self, files, container_id):
        for file_path in files:
            payload = {}
            file_name = file_path.split('.')[0]
            file_name = util.get_file_name_no_extension(file_path)
            metadata_def = util.get_meta_type_by_suffix(file_path.split('.')[-1])
            metadata_type = metadata_def['xmlName']
            if metadata_type == 'ApexPage':
                tooling_type = 'ApexPageMember'
            elif metadata_type == 'ApexComponent':
                tooling_type = 'ApexComponentMember'
            elif metadata_type == 'ApexClass':
                tooling_type = 'ApexClassMember'
            elif metadata_type == 'ApexTrigger':
                tooling_type = 'ApexTriggerMember'

            # get content entity id
            content_entity_id = None
            if file_name in config.api_name_to_id_dict:
                content_entity_id = config.api_name_to_id_dict[file_name]
            else:
                content_entity_id = self.get_apex_entity_id_by_name(object_type=metadata_type, name=file_name)
            
            # create new component if needed
            if content_entity_id == None:
                payload['Body']                 = open(file_path, 'r').read()
                payload['Name']                 = file_name
                if metadata_type == 'ApexTrigger':
                    # grab object from body
                    m = re.search('on (.*?) \(', payload['Body'])
                    payload['TableEnumOrId']    = m.group(1)
                payload = json.dumps(payload)
                config.logger.debug('Creating new member')
                config.logger.debug(payload)
                r = requests.post(self.get_tooling_url()+"/sobjects/"+metadata_type, data=payload, headers=self.get_rest_headers('POST'), proxies=self.__get_proxies(), verify=False)
                response = util.parse_rest_response(r.text)
                content_entity_id = response['id']
                payload = {}
            
            # create/update member 
            #payload['LastSyncDate']         = TODO
            payload['Body']                 = open(file_path, 'r').read()
            payload['MetadataContainerId']  = container_id
            payload['ContentEntityId']      = content_entity_id
            payload = json.dumps(payload)
            config.logger.debug('Updating existing member')
            config.logger.debug(payload)
            r = requests.post(self.get_tooling_url()+"/sobjects/"+tooling_type, data=payload, headers=self.get_rest_headers('POST'), proxies=self.__get_proxies(), verify=False)
            response = util.parse_rest_response(r.text)
            
            #if the member already exists, patch it (TODO: cache member ids and go right to patch, handle exception)
            if type(response) is list and 'errorCode' in response[0]:
                debug('----> post to tooling member failed')
                #debug(response[0]['errorCode'])

                if response[0]['errorCode'] == 'DUPLICATE_VALUE':
                    dup_id = response[0]['message'].split(':')[-1]
                    dup_id = dup_id.strip()
                    
                    payload = json.loads(payload)
                    payload.pop("MetadataContainerId", None)
                    payload.pop("ContentEntityId", None)
                    payload = json.dumps(payload)
                    r = requests.patch(self.get_tooling_url()+"/sobjects/{0}/{1}".format(tooling_type, dup_id), data=payload, headers=self.get_rest_headers('PATCH'), proxies=self.__get_proxies(), verify=False)
                    if self.__is_failed_request(r):
                       self.__exception_handler(r)

                    member_id = dup_id
                elif response[0]['errorCode'] == 'INSUFFICIENT_ACCESS_ON_CROSS_REFERENCE_ENTITY' or response[0]['errorCode'] == 'MALFORMED_ID':
                    debug('----> bad metadata container')
                    raise MetadataContainerException('Invalid metadata container')
                else:
                    return util.generate_error_response(response[0]['errorCode'])
            else:
                member_id = response['id']

        #ok, now we're ready to submit an async request
        payload = {}
        payload['MetadataContainerId'] = container_id
        payload['IsCheckOnly'] = False
        payload['IsRunTests'] = False
        payload = json.dumps(payload)
        config.logger.debug(payload)
        r = requests.post(self.get_tooling_url()+"/sobjects/ContainerAsyncRequest", data=payload, headers=self.get_rest_headers('POST'), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        response = util.parse_rest_response(r.text)

        finished = False
        while finished == False:
            time.sleep(1)
            query_string = "Select Id, MetadataContainerId, MetadataContainerMemberId, State, IsCheckOnly, CompilerErrors, ErrorMsg FROM ContainerAsyncRequest WHERE Id='"+response["id"]+"'"
            r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            query_result = util.parse_rest_response(r.text)
            if query_result["done"] == True and query_result["size"] == 1 and 'records' in query_result:
                if query_result['records'][0]["State"] != 'Queued':
                    response = query_result['records'][0]
                    finished = True

        #clean up the apex member
        # if 'id' in response:
        #     #delete member
        #     r = requests.delete(self.get_tooling_url()+"/sobjects/{0}/{1}".format(tooling_type, member_id), headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        #     r.raise_for_status()

        return response    

    def get_metadata_container_id(self):
        query_string = "Select Id from MetadataContainer Where Name = 'MavensMate-"+self.user_id+"'"
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        query_result = util.parse_rest_response(r.text)
        #print query_result
        try:
            return query_result['records'][0]['Id']
        except:
            payload = {}
            payload['Name'] = "MavensMate-"+self.user_id
            payload = json.dumps(payload)
            r = requests.post(self.get_tooling_url()+"/sobjects/MetadataContainer", data=payload, headers=self.get_rest_headers('POST'), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            create_response = util.parse_rest_response(r.text)
            if create_response["success"] == True:
                return create_response["id"]
            else:
                return "error"

    #creates a flag only. the flag tells salesforce to generate some kind of debug log
    def new_metadatacontainer_for_this_user(self):
        payload = {}
        payload['Name'] = "MavensMate-"+self.user_id
        payload = json.dumps(payload)
        r = requests.post(self.get_tooling_url()+"/sobjects/MetadataContainer", data=payload, headers=self.get_rest_headers('POST'), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return util.parse_rest_response(r.text)            

    #deletes ALL checkpoints in the org
    def delete_mavensmate_metadatacontainers_for_this_user(self):
        query_string = "Select Id from MetadataContainer Where Name = 'MavensMate-"+self.user_id+"'"
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        qr = util.parse_rest_response(r.text)
        responses = []
        for r in qr['records']:
            resp = self.delete_tooling_entity("MetadataContainer", r["Id"])
            responses.append(resp.status_code)
        return responses


    #################
    #APEX CHECKPOINTS
    #################

    def get_completions(self, type):
        payload = { 'type' : 'apex' }
        r = requests.get(self.get_tooling_url()+"/completions", params=payload, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return r.text

    def get_apex_checkpoints(self, **kwargs):        
        if 'file_path' in kwargs:
            id = kwargs.get('id', None)
            file_path = kwargs.get('file_path', None)
            if id == None:
                ext = util.get_file_extension_no_period(file_path)
                api_name = util.get_file_name_no_extension(file_path)
                mtype = util.get_meta_type_by_suffix(ext)
                id = self.get_apex_entity_id_by_name(object_type=mtype['xmlName'], name=api_name)
            query_string = "Select Id, Line, Iteration, ExpirationDate, IsDumpingHeap from ApexExecutionOverlayAction Where ExecutableEntityId = '{0}'".format(id)
            payload = { 'q' : query_string }
            r = requests.get(self.get_tooling_url()+"/query/", params=payload, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            return util.parse_rest_response(r.text)
        else:
            query_string = "Select Id, ScopeId, ExecutableEntityId, Line, Iteration, ExpirationDate, IsDumpingHeap from ApexExecutionOverlayAction limit 5000"
            payload = { 'q' : query_string }
            r = requests.get(self.get_tooling_url()+"/query/", params=payload, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            return util.parse_rest_response(r.text)

    #creates a checkpoint at a certain line on an apex class/trigger
    def create_apex_checkpoint(self, payload):        
        if 'ScopeId' not in payload:
            payload['ScopeId'] = self.user_id
        if 'API_Name' in payload:
            payload['ExecutableEntityId'] = self.get_apex_entity_id_by_name(object_type=payload['Object_Type'], name=payload['API_Name'])
            payload.pop('Object_Type', None)
            payload.pop('API_Name', None)
        
        payload.pop('workspace', None)

        payload = json.dumps(payload)
        r = requests.post(self.get_tooling_url()+"/sobjects/ApexExecutionOverlayAction", data=payload, proxies=self.__get_proxies(), headers=self.get_rest_headers('POST'), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        
        ##WE ALSO NEED TO CREATE A TRACE FLAG FOR THIS USER
        expiration = util.get_iso_8601_timestamp(30)

        payload = {
            "ApexCode"          : "FINEST",
            "ApexProfiling"     : "INFO",
            "Callout"           : "INFO",
            "Database"          : "INFO",
            "ExpirationDate"    : expiration,
            "ScopeId"           : self.user_id,
            "System"            : "DEBUG",
            "TracedEntityId"    : self.user_id,
            "Validation"        : "INFO",
            "Visualforce"       : "INFO",
            "Workflow"          : "INFO"
        }
        self.create_trace_flag(payload)

        return util.generate_success_response("Done")

    #deletes ALL checkpoints in the org
    def delete_apex_checkpoints(self):
        query_string = 'Select Id FROM ApexExecutionOverlayAction'
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, proxies=self.__get_proxies(), headers=self.get_rest_headers(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        qr = util.parse_rest_response(r.text)
        for r in qr['records']:
            self.delete_tooling_entity("ApexExecutionOverlayAction", r["Id"])

    #deletes a single checkpoint
    def delete_apex_checkpoint(self, **kwargs):
        if 'overlay_id' in kwargs:
            r = requests.delete(self.get_tooling_url()+"/sobjects/ApexExecutionOverlayAction/{0}".format(kwargs['overlay_id']), headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            return util.generate_success_response('OK')
        else:
            id = kwargs.get('id', None)
            file_path = kwargs.get('file_path', None)
            line_number = kwargs.get('line_number', None)
            if id == None:
                ext = util.get_file_extension_no_period(file_path)
                api_name = util.get_file_name_no_extension(file_path)
                mtype = util.get_meta_type_by_suffix(ext)
                id = self.get_apex_entity_id_by_name(object_type=mtype['xmlName'], name=api_name)
            
            query_string = "Select Id from ApexExecutionOverlayAction Where ExecutableEntityId = '{0}' AND Line = {1}".format(id, line_number)
            r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            query_result = util.parse_rest_response(r.text)
            overlay_id = query_result['records'][0]['Id']
            r = requests.delete(self.get_tooling_url()+"/sobjects/ApexExecutionOverlayAction/{0}".format(overlay_id), headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            return util.generate_success_response('OK')

    ########################
    #APEX CHECKPOINT RESULTS
    ########################

    def get_apex_checkpoint_results(self, user_id=None, limit=20):
        if user_id == None:
            user_id = self.user_id
        #dont query heapdump, soqlresult, or apexresult here - JF
        query_string = 'Select Id, CreatedDate, ActionScript, ActionScriptType, ExpirationDate, IsDumpingHeap, Iteration, Line, UserId From ApexExecutionOverlayResult order by CreatedDate desc limit '+str(limit)
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        qr = util.parse_rest_response(r.text)
        for record in qr['records']:
            heap_query = 'SELECT HeapDump, ApexResult, SOQLResult, ActionScript FROM ApexExecutionOverlayResult WHERE Id = \''+record['Id']+'\''
            rr = requests.get(self.get_tooling_url()+"/query/", params={'q':heap_query}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
            if rr.status_code != 200:
                self.__exception_handler(rr)
            qrr = util.parse_rest_response(rr.text)
            record["HeapDump"] = qrr['records'][0]['HeapDump']
            record["ApexResult"] = qrr['records'][0]['ApexResult']
            record["SOQLResult"] = qrr['records'][0]['SOQLResult']
            record["ActionScript"] = qrr['records'][0]['ActionScript']
        return qr

    def delete_apex_checkpoint_results(self):
        query_string = 'Select Id From ApexExecutionOverlayResult Where UserId = \''+self.user_id+'\' order by CreatedDate'
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        qr = util.parse_rest_response(r.text)
        for record in qr['records']:
            self.delete_tooling_entity("ApexExecutionOverlayResult", record["Id"])
        return util.generate_success_response("Done")

    ############
    #TRACE FLAGS
    ############

    #creates a flag only. the flag tells salesforce to generate some kind of debug log
    def create_trace_flag(self, payload):
        if 'ScopeId' not in payload:
            payload['ScopeId'] = self.user_id
        payload = json.dumps(payload)
        r = requests.post(self.get_tooling_url()+"/sobjects/TraceFlag", data=payload, headers=self.get_rest_headers('POST'), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return util.parse_rest_response(r.text)

    #get the trace flags that have been set up in the org
    def get_trace_flags(self, user_ids=[]):
        if user_ids == []:
            query_string = 'Select Id,ApexCode,ApexProfiling,Callout,Database,System,Validation,Visualforce,Workflow,ExpirationDate,TracedEntityId,ScopeId FROM TraceFlag order by CreatedDate desc'
        else:
            id_string = "','".join(user_ids)
            id_string = "'"+id_string+"'"
            query_string = 'Select Id,ApexCode,ApexProfiling,Callout,Database,System,Validation,Visualforce,Workflow,ExpirationDate,TracedEntityId,ScopeId FROM TraceFlag WHERE TracedEntityId IN ({0}) order by CreatedDate desc'.format(id_string)
        return self.tooling_query(query_string)

    def delete_trace_flags(self, user_id=None):
        if user_id == None:
            query_string = "Select Id From TraceFlag"
        else:
            query_string = "Select Id From TraceFlag WHERE TracedEntityId = '{0}'".format(config.sfdc_client.user_id)
        qr = self.tooling_query(query_string)
        if type(qr['records'] is list and len(qr['records']) > 0):
            for record in qr['records']:
                self.delete_tooling_entity("TraceFlag", record["Id"])
            return util.generate_success_response("Done")
        else:
            return util.generate_success_response("No stack traces to delete")


    ###########
    #TESTING
    ###########    

    def run_async_apex_tests(self, params, dump_to_json=False):
        classes = params.get("classes", None)
        if classes == None:
            classes = params.get("files", None)
        if classes == None or classes == []:
            raise MMException("Please submit Apex test classes to run")
        responses = []
        debug(classes)
        downloaded_log_ids = []
        for c in classes:
            class_id = self.get_apex_entity_id_by_name(object_type="ApexClass", name=c)
            if class_id == None: continue
            params = {
                "ApexClassId" : class_id
            }
            payload = json.dumps(params)
            r = requests.post(self.get_tooling_url()+"/sobjects/ApexTestQueueItem", data=payload, headers=self.get_rest_headers('POST'), proxies=self.__get_proxies(), verify=False)
            if self.__is_failed_request(r):
                self.__exception_handler(r)
            res = util.parse_rest_response(r.text)
            if "success" not in res and "message" in res:
                raise MMException(r["message"])
            debug('test queue submission response')
            debug(res)
            if res["success"] == True:
                parentJobId = None
                qr = self.query("Select ParentJobId FROM ApexTestQueueItem WHERE Id='{0}'".format(res["id"]))
                if qr["done"] == True and qr["totalSize"] == 1 and 'records' in qr:
                    parentJobId = qr['records'][0]["ParentJobId"]
                finished = False
                while finished == False:
                    time.sleep(1)
                    query_string = "SELECT ApexClassId, ApexClass.Name, Status, ExtendedStatus FROM ApexTestQueueItem WHERE ParentJobId = '{0}'".format(parentJobId)
                    query_result = self.query(query_string)
                    if query_result["done"] == True and query_result["totalSize"] == 1 and 'records' in query_result:
                        done_statuses = ['Aborted', 'Completed', 'Failed']
                        if query_result['records'][0]["Status"] in done_statuses:
                            #now check for method results
                            qr = self.query("SELECT Outcome, ApexClassId, ApexClass.Name, MethodName, Message, StackTrace, ApexLogId FROM ApexTestResult WHERE AsyncApexJobId ='{0}'".format(parentJobId))
                            parent_response = query_result['records'][0]
                            parent_response["detailed_results"] = []
                            for r in qr["records"]:
                                parent_response["detailed_results"].append(r)
                                if "ApexLogId" in r and r["ApexLogId"] != None and r["ApexLogId"] not in downloaded_log_ids:
                                    cname = r["ApexClass"]["Name"]
                                    if os.path.isdir(os.path.join(config.connection.workspace,config.project.project_name,"debug","tests",cname)) == False:
                                        os.makedirs(os.path.join(config.connection.workspace,config.project.project_name,"debug","tests",cname))
                                    ts = time.time()
                                    if not config.is_windows:
                                        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                                    else:
                                        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H %M %S')
                                    file_name = cname+"-"+st+".log"
                                    file_path = os.path.join(config.connection.workspace,config.project.project_name,"debug","tests",cname,file_name)
                                    debug_log_body = self.download_log(r["ApexLogId"])
                                    src = open(file_path, "w")
                                    src.write(debug_log_body)
                                    src.close()
                                    downloaded_log_ids.append(r["ApexLogId"]) 
                            responses.append(parent_response)
                            finished = True
            else:
                responses.append({"class":c,"success":False})

        if dump_to_json:
            return json.dumps(responses)
        else:
            return responses

    def get_apex_test_coverage(self, params, transform_ids=True):
        if int(float(util.SFDC_API_VERSION)) < 29:
            raise MMException('This operation requires mm_api_version 29.0 or later')

        sfdc_client = self

        classes         = params.get("classes", [])
        triggers        = params.get("triggers", [])
        test_classes    = params.get("test_classes", [])

        if len(classes) == 0 and len(triggers) == 0:
            raise MMException('You must request coverage for at least 1 Apex class or 1 Apex trigger')

        for i, clazz in enumerate(classes):
            classes[i] = os.path.basename(clazz).replace(".cls","")
        for i, trigger in enumerate(triggers):
            triggers[i] = os.path.basename(trigger).replace(".triggers","")

        if len(classes) > 0:
            class_name_result = sfdc_client.get_apex_entity_id_by_name(object_type="ApexClass",class_or_trigger_names=classes)
        if len(triggers) > 0:
            trigger_name_result = sfdc_client.get_apex_entity_id_by_name(object_type="ApexTrigger",class_or_trigger_names=triggers)
        if len(test_classes) > 0:
            test_class_name_result = sfdc_client.get_apex_entity_id_by_name(object_type="ApexClass",class_or_trigger_names=test_classes)

        if transform_ids:
            id_to_name_map = {}

        ids = []
        test_class_ids = []
        
        if len(classes) > 0:
            for result in class_name_result:
                ids.append(result.Id)
                if transform_ids:
                    id_to_name_map[result.Id] = result.Name
        if len(triggers) > 0:
            for result in trigger_name_result:
                ids.append(result.Id)
                if transform_ids:
                    id_to_name_map[result.Id] = result.Name

        if len(test_classes) > 0:
            for result in test_class_name_result:
                test_class_ids.append(result.Id)
            test_class_id_string = "','".join(test_class_ids)
            test_class_id_string = "'"+test_class_id_string+"'"

        id_string = "','".join(ids)
        id_string = "'"+id_string+"'"
        
        if test_classes != []:
            query = "SELECT NumLinesCovered, NumLinesUncovered, Coverage, ApexClassOrTriggerId FROM ApexCodeCoverage WHERE ApexClassOrTriggerId IN ({0}) AND ApexTestClassId IN ({1})".format(id_string, test_class_id_string)
        else:
            query = "SELECT NumLinesCovered, NumLinesUncovered, Coverage, ApexClassOrTriggerId FROM ApexCodeCoverageAggregate WHERE ApexClassOrTriggerId IN ({0})".format(id_string)
        debug(query)
        query_result = self.tooling_query(query)
        debug(query_result)
        if transform_ids:
            coverage = util.calculate_coverage(query_result, id_to_name_map)
            debug('coverage')
            debug(coverage)
            for r in coverage:
                try:
                    percent_covered = int(round(100 * ((float((r["NumLinesCovered"] + r["NumLinesUncovered"])) - float(r["NumLinesUncovered"])) / (r["NumLinesCovered"] + r["NumLinesUncovered"]))))
                except:
                    percent_covered = 0
                r["percentCovered"] = percent_covered
                if percent_covered < 40:
                    r['coverageLevel'] = 'danger'
                elif percent_covered >= 40 and percent_covered < 75:
                    r['coverageLevel'] = 'warning'
                elif percent_covered >= 75:
                    r['coverageLevel'] = 'success'
                else:
                    r['coverageLevel'] = 'info'
            debug('after')
            debug(coverage)
            return coverage
        else:
            return query_result

    def get_org_wide_test_coverage(self):
        query = "SELECT PercentCovered FROM ApexOrgWideCoverage"
        return self.tooling_query(query)["records"][0]
         
    ###########
    #DEBUG LOGS
    ###########

    def delete_debug_logs(self, scope="user"):
        if scope != "user":
            query_string = "Select Id From ApexLog"
        else:
            query_string = "Select Id From ApexLog WHERE LogUserId = '{0}'".format(self.user_id)
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        qr = util.parse_rest_response(r.text)
        for record in qr['records']:
            self.delete_tooling_entity("ApexLog", record["Id"])
        return util.generate_success_response("Done")

    #get a list of debug logs, STILL NEED TO DOWNLOAD THE LOG
    def get_debug_logs(self, download_body=False, limit=20, scope="user"):
        if scope == "user":
            query_string = "Select Id,Application,Location,LogLength,LogUserId,Operation,Request,StartTime,Status From ApexLog WHERE LogUserId = '{0}' Order By StartTime desc limit {1}".format(self.user_id, limit)
        else:
            query_string = "Select Id,Application,Location,LogLength,LogUserId,Operation,Request,StartTime,Status From ApexLog Order By StartTime desc limit {1}".format(self.user_id, limit)
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':query_string}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        qr = util.parse_rest_response(r.text)
        for record in qr['records']:
            if download_body:
                record['Body'] = self.download_log(record['Id'])
        return qr

    def download_log(self, id):
        r = requests.get(self.get_tooling_url()+"/sobjects/ApexLog/"+id+"/Body", headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return r.text

    

    #############
    #SYMBOL TABLE
    #############

    #pass a list of apex class/trigger ids and return the symbol tables
    def get_symbol_table(self, ids=[]):        
        id_string = "','".join(ids)
        id_string = "'"+id_string+"'"
        query_string = "Select ContentEntityId, ContentEntity.Name, SymbolTable From ApexClassMember Where ContentEntityId IN (" + id_string + ")"
        payload = { 'q' : query_string }
        r = requests.get(self.get_tooling_url()+"/query/", params=payload, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return util.parse_rest_response(r.text)

    #pass a list of apex class/trigger ids and return the symbol tables
    def get_symbol_tables_by_class_name(self, names=[]):        
        name_string = "','".join(names)
        name_string = "'"+name_string+"'"
        query_string = "Select NamespacePrefix, SymbolTable, Name From ApexClass Where Name IN (" + name_string + ") AND NamespacePrefix = '"+self.get_org_namespace()+"'"
        payload = { 'q' : query_string }
        r = requests.get(self.get_tooling_url()+"/query/", params=payload, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return util.parse_rest_response(r.text)

    #pass a list of apex class/trigger ids and return the symbol tables
    def get_symbol_tables_by_class_id(self, ids=[]):        
        id_string = "','".join(ids)
        id_string = "'"+id_string+"'"
        query_string = "Select NamespacePrefix, SymbolTable, Name From ApexClass Where Id IN (" + id_string + ") AND NamespacePrefix = '"+self.get_org_namespace()+"'"
        payload = { 'q' : query_string }
        r = requests.get(self.get_tooling_url()+"/query/", params=payload, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return util.parse_rest_response(r.text)

    #####
    #UTIL
    #####

    def delete_tooling_entity(self, type, id):
        r = requests.delete(self.get_tooling_url()+"/sobjects/{0}/{1}".format(type, id), headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        return r

    # def get_field_definition(self, object_enum_or_id):
    #     query_string = "Select DeveloperName, Metadata FROM CustomField WHERE TableEnumOrId = '{0}'".format('01IA0000002C6aMMAS')
    #     qr = self.tooling_query(query_string)
    #     if qr["done"] == True and qr["totalSize"] == 1 and 'records' in qr:
    #         print qr

    ##END TOOLING PLUMBING##

    def tooling_query(self, soql):
        r = requests.get(self.get_tooling_url()+"/query/", params={'q':soql}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        r.raise_for_status()
        return r.json()

    def query(self, soql):
        r = requests.get(self.get_base_url()+"/query/", params={'q':soql}, headers=self.get_rest_headers(), proxies=self.__get_proxies(), verify=False)
        if self.__is_failed_request(r):
            self.__exception_handler(r)
        r.raise_for_status()
        return r.json()

    def get_rest_headers(self, method='GET'):
        headers = {}
        headers['Authorization'] = 'Bearer '+self.sid
        if method == 'POST' or method == 'PATCH':
            headers['Content-Type'] = 'application/json'
        return headers

    def get_base_url(self):
        pod = self.metadata_server_url.replace("https://", "")
        pod = pod.split('.salesforce.com')[0]
        return "https://{0}.salesforce.com/services/data/v{1}".format(pod, util.SFDC_API_VERSION)

    def get_tooling_url(self):
        pod = self.metadata_server_url.replace("https://", "")
        pod = pod.split('.salesforce.com')[0]
        return "https://{0}.salesforce.com/services/data/v{1}/tooling".format(pod, util.SFDC_API_VERSION)

    def __is_failed_request(self, r):
        return r.status_code >= 300

    def __get_proxies(self):
        try:
            mm_http_proxy = config.connection.get_plugin_client_setting('mm_http_proxy', None)
            mm_http_proxy = mm_http_proxy.replace("\\","")
            mm_https_proxy = config.connection.get_plugin_client_setting('mm_https_proxy', None)
            mm_https_proxy = mm_https_proxy.replace("\\","")
            if mm_https_proxy == None and mm_http_proxy != None:
                mm_https_proxy = mm_http_proxy
            if mm_http_proxy != None and mm_https_proxy != None:
                return {
                    "http": mm_http_proxy,
                    "https": mm_https_proxy
                }
            elif mm_http_proxy != None:
                return {
                    "http": mm_http_proxy
                }
            elif mm_https_proxy != None:
                return {
                    "https": mm_https_proxy
                }
            else:
                return urllib.getproxies()
        except:
            return urllib.getproxies()             

    def __get_partner_client(self):
        if int(float(util.SFDC_API_VERSION)) >= 29:
            wsdl_location = os.path.join(util.WSDL_PATH, 'partner-29.xml')
        else:
            wsdl_location = os.path.join(util.WSDL_PATH, 'partner.xml')
        try:
            if os.path.exists(os.path.join(config.project.location,'config','partner.xml')):
                wsdl_location = os.path.join(config.project.location,'config','partner.xml')
        except:
            pass

        return SforcePartnerClient(
            wsdl_location, 
            apiVersion=util.SFDC_API_VERSION, 
            environment=self.org_type, 
            sid=self.sid, 
            metadata_server_url=self.metadata_server_url, 
            server_url=self.endpoint)

    def __get_metadata_client(self):
        if int(float(util.SFDC_API_VERSION)) >= 29:
            wsdl_location = os.path.join(util.WSDL_PATH, 'metadata-29.xml')
        else:
            wsdl_location = os.path.join(util.WSDL_PATH, 'metadata.xml')

        try:
           if os.path.exists(os.path.join(config.project.location,'config','metadata.xml')):
               wsdl_location = os.path.join(config.project.location,'config','metadata.xml')
        except:
           pass

        return SforceMetadataClient(
            wsdl_location, 
            apiVersion=util.SFDC_API_VERSION, 
            environment=self.org_type, 
            sid=self.sid, 
            url=self.metadata_server_url, 
            server_url=self.endpoint)

    def __get_apex_client(self):
        if int(float(util.SFDC_API_VERSION)) >= 29:
            wsdl_location = os.path.join(util.WSDL_PATH, 'apex-29.xml')
        else:
            wsdl_location = os.path.join(util.WSDL_PATH, 'apex.xml')

        try:
            if os.path.exists(os.path.join(config.project.location,'config','apex.xml')):
                wsdl_location = os.path.join(config.project.location,'config','apex.xml')
        except:
            pass

        return SforceApexClient(
            wsdl_location, 
            apiVersion=util.SFDC_API_VERSION, 
            environment=self.org_type, 
            sid=self.sid, 
            metadata_server_url=self.metadata_server_url, 
            server_url=self.endpoint)

    def __get_tooling_client(self):
        if int(float(util.SFDC_API_VERSION)) >= 29:
            wsdl_location = os.path.join(util.WSDL_PATH, 'tooling-29.xml')
        else:
            wsdl_location = os.path.join(util.WSDL_PATH, 'tooling.xml')

        try:
            if os.path.exists(os.path.join(config.project.location,'config','tooling.xml')):
                wsdl_location = os.path.join(config.project.location,'config','tooling.xml')
        except:
            pass

        return SforceToolingClient(
            wsdl_location, 
            apiVersion=util.SFDC_API_VERSION, 
            environment=self.org_type, 
            sid=self.sid, 
            metadata_server_url=self.metadata_server_url, 
            server_url=self.endpoint)

    def __exception_handler(self, result, name=""):
        url = result.url
        try:
            response_content = result.json()
        except Exception:
            response_content = result.text

        if result.status_code == 300:
            message = "More than one record for {url}. Response content: {content}"
            message = message.format(url=url, content=response_content)
            raise SalesforceMoreThanOneRecord(message)
        elif result.status_code == 400:
            message = "Malformed request {url}. Response content: {content}"
            message = message.format(url=url, content=response_content)
            raise SalesforceMalformedRequest(message)
        elif result.status_code == 401:
            message = "Expired session for {url}. Response content: {content}"
            message = message.format(url=url, content=response_content)
            raise SalesforceExpiredSession(message)
        elif result.status_code == 403:
            message = "Request refused for {url}. Resonse content: {content}"
            message = message.format(url=url, content=response_content)
            raise SalesforceRefusedRequest(message)
        elif result.status_code == 404:
            message = 'Resource {name} Not Found. Response content: {content}'
            message = message.format(name=name, content=response_content)
            raise SalesforceResourceNotFound(message)
        else:
            message = 'Error Code {status}. Response content: {content}'
            message = message.format(status=result.status_code, content=response_content)
            raise SalesforceGeneralError(message)
