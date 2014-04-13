import os.path
import lib.util as util
import json
import lib.config as config
from lib.exceptions import *
from lib.basecommand import Command

class UpdateDebugSettingsCommand(Command):
    def execute(self):
        users       = self.params.get('users', None)
        levels      = self.params.get('debug_categories', None)
        expiration  = self.params.get('expiration', None)
        config.project.put_debug_file(users, levels, expiration)
        return util.generate_success_response("Debug settings updated successfully")

class NewQuickTraceFlagCommand(Command):
    name="new_quick_trace_flag"
    aliases=["new_quick_log"]
    def execute(self):
        debug_users = config.project.get_debug_users()
        debug_settings = config.project.get_debug_settings()
        if self.params.get('running_user_only', False):
            payload = {}
            payload["debug_categories"] = debug_settings["levels"]
            payload["expiration"]       = debug_settings["expiration"]
            payload["user_id"]          = config.sfdc_client.user_id
            payload["type"]             = "user"
            response = NewTraceFlagCommand(params=payload).execute()
            response = json.loads(response)
            if "success" in response and response["success"] == False:
                return util.generate_error_response(response["errors"][0])
            return util.generate_success_response('Logging for runner user setup successfully')
        else:
            for u in debug_users:
                payload = {}
                payload["debug_categories"] = debug_settings["levels"]
                payload["expiration"]       = debug_settings["expiration"]
                payload["user_id"]          = u
                payload["type"]             = "user"
                response = NewTraceFlagCommand(params=payload).execute()
                response = json.loads(response)
                if "success" in response and response["success"] == False:
                    return util.generate_error_response(response["errors"][0])
            return util.generate_success_response('{0} Log(s) created successfully'.format(str(len(debug_users))))

class FetchLogsCommand(Command):
    name="fetch_logs"
    def execute(self):
        number_of_logs = 0
        limit   = config.connection.get_plugin_client_setting('mm_number_of_logs_limit', 20)
        id_list = ','.join("'"+item+"'" for item in config.project.get_debug_users())
        log_result = config.sfdc_client.execute_query('Select Id, LogUserId, SystemModstamp From ApexLog Where SystemModstamp >= TODAY and Location != \'HeapDump\' AND LogUserId IN ({0}) order by SystemModstamp desc limit {1}'.format(id_list, str(limit)))
        logs = []
        if 'records' in log_result:
            for r in log_result['records']:
                id = r["Id"]
                log = config.sfdc_client.download_log(id)
                logs.append({"id":id,"modstamp":str(r["SystemModstamp"]),"log":log,"userid":r["LogUserId"]})
            if os.path.isdir(os.path.join(config.connection.workspace,config.project.project_name,"debug","logs")) == False:
                os.makedirs(os.path.join(config.connection.workspace,config.project.project_name,"debug","logs"))
            for the_file in os.listdir(os.path.join(config.connection.workspace,config.project.project_name,"debug","logs")):
                file_path = os.path.join(config.connection.workspace,config.project.project_name,"debug","logs", the_file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception, e:
                    print e
            number_of_logs = len(logs)
            for log in logs:
                modstamp = log["modstamp"]
                if config.is_windows:
                    modstamp = modstamp.replace(':', ' ')
                file_name = modstamp+"-"+log["userid"]+".log"
                src = open(os.path.join(config.connection.workspace,config.project.project_name,"debug","logs",file_name), "w")
                src.write(log["log"])
                src.close() 
        else:
            config.logger.debug("No logs to download")

        return util.generate_success_response(str(number_of_logs)+' Logs successfully downloaded') 

class NewTraceFlagCommand(Command):
    aliases=["new_log"]
    def execute(self):
        """
            params = {
                "ApexCode"          : "None",
                "ApexProfiling"     : "01pd0000001yXtYAAU",
                "Callout"           : True,
                "Database"          : 1,
                "ExpirationDate"    : 3,
                "ScopeId"           : "",
                "System"            : "",
                "TracedEntityId"    : "",
                "Validation"        : "",
                "Visualforce"       : "",
                "Workflow"          : ""
            }
        """
        if 'type' not in self.params:
            raise MMException("Please include the type of log, 'user' or 'apex'")
        if 'debug_categories' not in self.params:
            raise MMException("Please include debug categories in dictionary format: e.g.: {'ApexCode':'DEBUG', 'Visualforce':'INFO'}")

        request = {}
        if self.params['type'] == 'user':
            request['ScopeId'] = None
            request['TracedEntityId'] = self.params.get('user_id', config.sfdc_client.user_id)
        elif self.params['type'] == 'apex':
            #request['ScopeId'] = 'user'
            request['ScopeId'] = config.sfdc_client.user_id
            request['TracedEntityId'] = self.params['apex_id']

        for c in self.params['debug_categories']:
            if 'category' in c:
                request[c['category']] = c['level']
            else:
                request[c] = self.params['debug_categories'][c]
        
        request['ExpirationDate'] = util.get_iso_8601_timestamp(int(float(self.params.get('expiration', 30))))

        config.logger.debug(self.params['debug_categories'])
        config.logger.debug("Log creation reuqest--->")
        config.logger.debug(request)

        create_result = config.sfdc_client.create_trace_flag(request)

        config.logger.debug("Log creation response--->")
        config.logger.debug(create_result)

        if type(create_result) is list:
            create_result = create_result[0]
        if type(create_result) is not str and type(create_result) is not unicode:
            return json.dumps(create_result)
        else:
            return create_result

class GetTraceFlagsCommand(Command):
    def execute(self):
        return config.sfdc_client.get_trace_flags([config.sfdc_client.user_id])

class DeleteTraceFlagsCommand(Command):
    def execute(self):
        return config.sfdc_client.delete_trace_flags(config.sfdc_client.user_id)

class IndexApexOverlaysCommand(Command):
    def execute(self):
        result = config.sfdc_client.get_apex_checkpoints()
        if 'records' not in result or len(result['records']) == 0:
            project.put_overlays_file('[]')
            return util.generate_success_response('Could Not Find Any Apex Execution Overlays')
        else:
            id_to_name_map = {}
            class_ids = []
            trigger_ids = []

            for r in result['records']:
                entity_id = r["ExecutableEntityId"]
                if entity_id.startswith('01q'):
                    trigger_ids.append("Id = '"+entity_id+"'")
                elif entity_id.startswith('01p'):
                    class_ids.append("Id = '"+entity_id+"'")

            class_filter = ' or '.join(class_ids)
            trigger_filter = ' or '.join(trigger_ids)
            
            if len(class_ids) > 0:
                soql = 'Select Id, Name From ApexClass WHERE '+class_filter
                class_result = config.sfdc_client.execute_query(soql)

                if 'records' in class_result:
                    for r in class_result['records']:
                        id_to_name_map[r['Id']] = r['Name']


            if len(trigger_ids) > 0:
                soql = 'Select Id, Name From ApexTrigger WHERE '+trigger_filter
                trigger_result = config.sfdc_client.execute_query(soql)

                if 'records' in trigger_result:
                    for r in trigger_result['records']:
                        id_to_name_map[r['Id']] = r['Name']

            for r in result['records']:
                r['API_Name'] = id_to_name_map[r['ExecutableEntityId']]

            overlays = json.dumps(result['records'])
            config.project.put_overlays_file(overlays)
            return util.generate_success_response('Apex Execution Overlays Successfully Indexed to config/.overlays')

class NewApexOverlayCommand(Command):
    def execute(self):
        """
            self.params = {
                "ActionScriptType"      : "None",
                "ExecutableEntityId"    : "01pd0000001yXtYAAU",
                "IsDumpingHeap"         : True,
                "Iteration"             : 1,
                "Line"                  : 3,
                "ScopeId"               : "005d0000000xxzsAAA"
            }
        """
        if 'project_name' in self.params:
            self.params.pop('project_name', None)

        create_result = config.sfdc_client.create_apex_checkpoint(self.params)
        if type(create_result) is list:
            create_result = create_result[0]
        IndexApexOverlaysCommand(params=self.params).execute()
        if type(create_result) is not str and type(create_result) is not unicode:
            return json.dumps(create_result)
        else:
            return create_result

class DeleteApexOverlayCommand(Command):
    name="delete_apex_overlay"
    def execute(self):
        delete_result = config.sfdc_client.delete_apex_checkpoint(overlay_id=self.params['id'])
        IndexApexOverlaysCommand(params=self.params).execute()
        return delete_result
  
class FetchCheckpointsCommand(Command):
    def execute(self):
        number_of_checkpoints = 0
        #user_id = self.params.get('user_id', config.sfdc_client.user_id)
        limit   = self.params.get('limit', 20)
        checkpoint_results = config.sfdc_client.get_apex_checkpoint_results(config.sfdc_client.user_id, limit)
        if 'records' in checkpoint_results:
            number_of_checkpoints = len(checkpoint_results['records'])
            if os.path.isdir(os.path.join(config.project.location,"debug","checkpoints")):
                shutil.rmtree(os.path.join(config.project.location,"debug","checkpoints"))

            os.makedirs(os.path.join(config.project.location,"debug","checkpoints"))

            apex_entity_to_lines = {}
            for r in checkpoint_results['records']:
                if 'HeapDump' in r and 'className' in r['HeapDump']:
                    if r['HeapDump']['className'] not in apex_entity_to_lines:
                        apex_entity_to_lines[r['HeapDump']['className']] = [r['Line']]
                    else:
                        apex_entity_to_lines[r['HeapDump']['className']].append(r['Line'])

            for apex_entity_name, lines in apex_entity_to_lines.items():
                if not os.path.isdir(os.path.join(config.project.location,"debug","checkpoints",apex_entity_name)):
                    os.makedirs(os.path.join(config.project.location,"debug","checkpoints",apex_entity_name))
                for l in lines:
                    if not os.path.isdir(os.path.join(config.project.location,"debug","checkpoints",apex_entity_name,str(l))):
                        os.makedirs(os.path.join(config.project.location,"debug","checkpoints",apex_entity_name,str(l)))

            for r in checkpoint_results['records']:
                if 'HeapDump' in r and 'className' in r['HeapDump']:
                    modstamp = r["HeapDump"]["heapDumpDate"]
                    if config.is_windows:
                        modstamp = modstamp.replace(':', ' ')
                    file_name = modstamp+"-"+r["UserId"]+".json"
                    file_path = os.path.join(config.project.location,"debug","checkpoints",r['HeapDump']['className'],str(r['Line']),file_name)
                    src = open(file_path, "w")
                    src.write(json.dumps(r,sort_keys=True,indent=4))
                    src.close() 
        else:
            config.logger.debug("No checkpoints to download")
    
        return util.generate_success_response(str(number_of_checkpoints)+' Checkpoints successfully downloaded') 