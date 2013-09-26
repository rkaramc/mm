import os
import mm_util
import threading
import subprocess
import config
import re
import json
import pprint

apex_extensions_to_check        = ['cls', 'trigger']
vf_extensions_to_check          = ['page', 'component']
without_sharing_pattern         = re.compile(".*?without sharing class.*?",re.IGNORECASE|re.MULTILINE|re.DOTALL)
dml_for_loop_pattern            = re.compile(r"(for|while) *?\(.*?\).*?{.*?(insert|update|delete|upsert).*?;.*?}", re.IGNORECASE|re.MULTILINE|re.DOTALL)
query_for_loop_pattern          = re.compile(r"(for|while) *?\(.*?\).*?{.*?\[ *SELECT\b.*?\].*?;.*?}", re.IGNORECASE|re.MULTILINE|re.DOTALL)
soql_query_pattern              = re.compile(r"\[ *SELECT\b.*?\]", re.IGNORECASE|re.MULTILINE|re.DOTALL)
db_query_pattern                = re.compile(r"Database.query\(.*?\) *;", re.IGNORECASE|re.MULTILINE|re.DOTALL)

where_seed      = 'where'
not_like_seed   = 'not like'
where_pattern       = re.compile(r'\b%s\b' % where_seed, re.I)
not_like_pattern    = re.compile(r'\b%s\b' % not_like_seed, re.I)

js_refresh_pattern = re.compile(r"(<meta[\s*]http-equiv=\"refresh\"[\s*]content=\"[0-9]+\"|window.location.reload|history.go\(0\))", re.IGNORECASE|re.MULTILINE|re.DOTALL)

class HealthCheck(object):

    def __init__(self, project_location):
        self.result = None
        self.project_location           = project_location
        self.without_sharing            = None
        self.dml_for_loop               = None
        self.soql_for_loop              = None
        self.soql_negative_operators    = None
        self.soql_no_where_clause       = None
        self.action_poller              = None
        self.javascript_refresh         = None
        self.meta_refresh               = None
        self.see_all_data               = None
        self.without_sharing_count      = 0
        self.dml_for_loop_count         = 0
        self.soql_for_loop_count        = 0
        self.without_sharing_count      = 0
        self.negative_soql_count        = 0
        self.no_where_clause_count      = 0
        self.action_poller_count        = 0
        self.javascript_refresh_count   = 0
        self.meta_refresh_count         = 0
        self.see_all_data_count         = 0
        self.hardcoded_link_count       = 0
        self.apex_files_to_check        = []
        self.vf_files_to_check          = []
        self.apex_parser_results        = {}
        self.vf_parser_results          = {}
        self.apex_result                = {}
        self.vf_result                  = {}
        self.result                     = {
            "apex_statistics" : { 
                "without_sharing" : {
                    "label"     : "Apex Classes using \"without sharing\"",
                    "count"     : 0,
                    "results"   : []
                },
                "dml_for_loop" : {
                    "label"     : "DML operations inside iterators",
                    "count"     : 0,
                    "results"   : []
                },
                "soql_for_loop" : {
                    "label"     : "SOQL statements inside iterators",
                    "count"     : 0,
                    "results"   : []
                },
                "soql_negative_operators" : {
                    "label"     : "SOQL statements using negative operators (NOT LIKE, !=)",
                    "count"     : 0,
                    "results"   : []
                },
                "soql_no_where_clause" : {
                    "label"     : "SOQL statements without \"WHERE\" clauses",
                    "count"     : 0,
                    "results"   : []
                },
                "see_all_data_annotations" : {
                    "label"     : "Apex Classes using (seeAllData=true) annotation",
                    "count"     : 0,
                    "results"   : []
                }
            }
            ,
            "visualforce_statistics" : {
                "action_poller"         : {
                    "label"     : "Visualforce Pages using actionpoller with interval <= 60",
                    "count"     : 0,
                    "results"   : []
                },
                "javascript_refresh"    : {
                    "label"     : "Visualforce Pages using javascript refresh",
                    "count"     : 0,
                    "results"   : []
                },
                "meta_refresh"    : {
                    "label"     : "Visualforce Pages using meta refresh",
                    "count"     : 0,
                    "results"   : []
                },
                "hardcoded_url"         : {
                    "label"     : "Visualforce Pages using outputLinks with hardcoded URLs",
                    "count"     : 0,
                    "results"   : []
                }
            }
        }

    def run(self):
        for dirname, dirnames, filenames in os.walk(os.path.join(self.project_location,"src")):
            for filename in filenames:
                full_file_path = os.path.join(dirname, filename)
                ext = mm_util.get_file_extension_no_period(full_file_path)
                if ext in apex_extensions_to_check:
                    self.apex_files_to_check.append(full_file_path)
                elif ext in vf_extensions_to_check:
                    self.vf_files_to_check.append(full_file_path)

        apex_parser_threads = []
        vf_parser_threads   = []

        apex_file_chunks    = list(mm_util.grouper(8, self.apex_files_to_check))
        vf_file_chunks      = list(mm_util.grouper(8, self.vf_files_to_check))

        for files in apex_file_chunks:                    
            apex_parser_thread = ApexParser(files)
            apex_parser_threads.append(apex_parser_thread)
            apex_parser_thread.start()

        for files in vf_file_chunks:                    
            vf_parser_thread = VfParser(files)
            vf_parser_threads.append(vf_parser_thread)
            vf_parser_thread.start()

        for thread in apex_parser_threads:
            thread.join()
            if thread.complete:
                self.apex_parser_results.update(thread.result)

        for thread in vf_parser_threads:
            thread.join()
            if thread.complete:
                self.vf_parser_results.update(thread.result)
        
        #pp = pprint.PrettyPrinter(indent=2)
        #pp.pprint(self.parser_results)

        for file_name in self.vf_files_to_check:
            parser_result = self.vf_parser_results[file_name]

            base_name = os.path.basename(file_name)
            self.vf_result[base_name] = {}
            file_body = mm_util.get_file_as_string(file_name)

            ### ACTION POLLERS
            if "actionPollers" not in parser_result:
                #print file_name
                continue

            action_pollers = parser_result["actionPollers"]
            action_poller_matches = []
            if len(action_pollers) > 0:
                for p in action_pollers:
                     
                    line_contents = ""
                    for lnum in range(p["location"]["row"], p["location"]["row"]+1):
                        line_contents += print_file_line(file_name, lnum)
                    
                    p["lineNumber"]       = p["location"]["row"]
                    p["line_contents"]    = line_contents

                    action_poller_matches.append(p)  


                self.result["visualforce_statistics"]["action_poller"]["results"].append(
                    {
                        "file_name" : base_name,
                        "flagged"   : len(action_poller_matches) > 0,
                        "matches"   : action_poller_matches   
                    }
                )
                self.action_poller_count += len(action_poller_matches)

            ### HARDCODED URLS
            output_links = parser_result["outputLinks"]
            link_matches = []
            if len(output_links) > 0:
                for p in output_links:
                     
                    line_contents = ""
                    for lnum in range(p["location"]["row"], p["location"]["row"]+1):
                        line_contents += print_file_line(file_name, lnum)
                    
                    p["lineNumber"]       = p["location"]["row"]
                    p["line_contents"]    = line_contents

                    link_matches.append(p)  


                self.result["visualforce_statistics"]["hardcoded_url"]["results"].append(
                    {
                        "file_name" : base_name,
                        "flagged"   : len(link_matches) > 0,
                        "matches"   : link_matches   
                    }
                )
                self.hardcoded_link_count += len(link_matches)

            ## REFRESHERS
            refreshers = re.finditer(js_refresh_pattern, file_body)          
            js_matches      = []
            meta_matches    = []
            for match in refreshers:
                if match != None and "meta" in match.group(0):
                    match_string = match.group(0).replace("<", "")    
                    meta_matches.append(match_string)
                else:
                    match_string = match.group(0)
                    js_matches.append(match_string)
            if len(js_matches) > 0:
                self.result["visualforce_statistics"]["javascript_refresh"]["results"].append(
                    {
                        "file_name" : base_name,
                        "flagged"   : len(js_matches) > 0,
                        "matches"   : js_matches   
                    }
                )
                self.javascript_refresh_count += len(js_matches)

            if len(meta_matches) > 0:
                self.result["visualforce_statistics"]["meta_refresh"]["results"].append(
                    {
                        "file_name" : base_name,
                        "flagged"   : len(meta_matches) > 0,
                        "matches"   : meta_matches   
                    }
                )
                self.meta_refresh_count += len(meta_matches)



        for file_name in self.apex_files_to_check:
            parser_result = self.apex_parser_results[file_name]

            base_name = os.path.basename(file_name)
            self.apex_result[base_name] = {}
            file_body = mm_util.get_file_as_string(file_name)

            ### WITHOUT SHARING
            without_sharings = re.finditer(without_sharing_pattern, file_body)          
            matches = []
            for match in without_sharings:
                matches.append(match.group(0))
            if len(matches) > 0:
                self.result["apex_statistics"]["without_sharing"]["results"].append(
                    {
                        "file_name" : base_name,
                        "flagged"   : len(matches) > 0,
                        "matches"   : matches   
                    }
                )
                self.without_sharing_count += len(matches)
            
            #print parser_result
            if "forLoops" not in parser_result:
                #print file_name
                continue

            for_loops       = parser_result["forLoops"]
            dml_statements  = parser_result["dmlStatements"]
            queries         = parser_result["queries"]
            methods         = parser_result["methods"]
            classes         = parser_result["classes"]

            #seealldata
            see_all_data_matches     = []
            for m in methods:
                if "annotations" in m and len(m["annotations"]) > 0:
                    for a in m["annotations"]:
                        if "pairs" in a:
                            for p in a["pairs"]:
                                if p["name"].lower() == "seealldata" and p["value"]["value"] == True:
                                    
                                    line_contents = ""
                                    for lnum in range(p["beginLine"], p["beginLine"]+2):
                                        line_contents += print_file_line(file_name, lnum)
                                    
                                    m["lineNumber"]       = p["beginLine"]
                                    m["line_contents"]    = line_contents

                                    see_all_data_matches.append(m)  

            for c in classes:
                if "annotations" in c and len(c["annotations"]) > 0:
                    for a in c["annotations"]:
                        if "pairs" in a:
                            for p in a["pairs"]:
                                if p["name"].lower() == "seealldata" and p["value"]["value"] == True:
                                    
                                    line_contents = ""
                                    for lnum in range(p["beginLine"], p["beginLine"]+2):
                                        line_contents += print_file_line(file_name, lnum)
                                    
                                    c["lineNumber"]       = p["beginLine"]
                                    c["line_contents"]    = line_contents

                                    see_all_data_matches.append(c)  
                        

            if len(see_all_data_matches) > 0:
                    self.result["apex_statistics"]["see_all_data_annotations"]["results"].append(
                        {
                            "file_name" : base_name,
                            "flagged"   : len(see_all_data_matches) > 0,
                            "matches"   : see_all_data_matches   
                        }
                    )
                    self.see_all_data_count += len(see_all_data_matches)

            #SOQL WITHOUT WHERE CLAUSES
            no_where_clause_matches     = []
            negative_operator_matches   = []
            for query in queries:
                line_number = query["lineNumber"]
                lower_query = query["statement"].lower()
                #if ' where ' not in lower_query:
                if where_pattern.search(lower_query) == None:
                    no_where_clause_matches.append(query)
                #if ' not like ' in lower_query or '!=' in lower_query:
                if not_like_pattern.search(lower_query) != None or "!=" in lower_query:
                    negative_operator_matches.append(query)

            if len(no_where_clause_matches) > 0:
                    self.result["apex_statistics"]["soql_no_where_clause"]["results"].append(
                        {
                            "file_name" : base_name,
                            "flagged"   : len(no_where_clause_matches) > 0,
                            "matches"   : no_where_clause_matches   
                        }
                    )
                    self.no_where_clause_count += len(no_where_clause_matches)

            if len(negative_operator_matches) > 0:
                    self.result["apex_statistics"]["soql_negative_operators"]["results"].append(
                        {
                            "file_name" : base_name,
                            "flagged"   : len(negative_operator_matches) > 0,
                            "matches"   : negative_operator_matches   
                        }
                    )
                    self.negative_soql_count += len(negative_operator_matches)


            ### DML INSIDE ITERATORS
            dml_matches     = []
            query_matches   = []

            if len(for_loops) > 0:
                for dml in dml_statements:
                    line_number = dml["statement"]["beginLine"]
                    for loop in for_loops:
                        if loop[0] < line_number < loop[1]:
                            #this is a dml statement inside an iterator
                            line_contents = ""
                            for lnum in range(loop[0], loop[1]+1):
                                line_contents += print_file_line(file_name, lnum)
                            
                            dml["lineNumber"]       = loop[0]
                            dml["line_contents"]    = line_contents
                            dml_matches.append(dml)

                for query in queries:
                    line_number = query["lineNumber"]
                    for loop in for_loops:
                        if loop[0] < line_number < loop[1]:
                            #this is a soql statement inside an iterator
                            query["line_contents"] = print_file_line(file_name, line_number)
                            query_matches.append(query)

                if len(dml_matches) > 0:
                    self.result["apex_statistics"]["dml_for_loop"]["results"].append(
                        {
                            "file_name" : base_name,
                            "flagged"   : len(dml_matches) > 0,
                            "matches"   : dml_matches   
                        }
                    )
                    self.dml_for_loop_count += len(dml_matches)

                if len(query_matches) > 0:
                    self.result["apex_statistics"]["soql_for_loop"]["results"].append(
                        {
                            "file_name" : base_name,
                            "flagged"   : len(query_matches) > 0,
                            "matches"   : query_matches   
                        }
                    )
                    self.soql_for_loop_count += len(query_matches)


        self.result["apex_statistics"]["without_sharing"]["count"]          = self.without_sharing_count
        self.result["apex_statistics"]["dml_for_loop"]["count"]             = self.dml_for_loop_count
        self.result["apex_statistics"]["soql_for_loop"]["count"]            = self.soql_for_loop_count
        self.result["apex_statistics"]["soql_negative_operators"]["count"]  = self.negative_soql_count
        self.result["apex_statistics"]["soql_no_where_clause"]["count"]     = self.no_where_clause_count
        self.result["apex_statistics"]["see_all_data_annotations"]["count"] = self.see_all_data_count

        self.result["visualforce_statistics"]["action_poller"]["count"]      = self.action_poller_count
        self.result["visualforce_statistics"]["javascript_refresh"]["count"] = self.javascript_refresh_count
        self.result["visualforce_statistics"]["meta_refresh"]["count"]       = self.meta_refresh_count
        self.result["visualforce_statistics"]["hardcoded_url"]["count"]      = self.hardcoded_link_count
        return self.result


def print_file_line(file_location, line_number):
    return_line = ""
    fp = open(file_location)
    for i, line in enumerate(fp):
        if i == line_number - 1:
            return_line = line
    fp.close()
    return return_line

class ApexParser(threading.Thread):

    def __init__(self, files):
        self.files          = files
        self.result         = {}
        self.complete       = False
        threading.Thread.__init__(self)

    def run(self):
        for f in self.files:
            parser_command = 'java -jar "{0}" "{1}"'.format(
                os.path.join(config.base_path,"bin","apex-parser.jar"),
                f)

            result_string = ""
            p = subprocess.Popen(parser_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            if p.stdout is not None : 
                for line in p.stdout.readlines():
                    result_string += line
            elif p.stderr is not None :
                print "****ERROR****"
                for line in p.stderr.readlines():
                    print line

            try:    
                self.result[f] = json.loads(result_string)
            except:
                #print "error on: ",self.file_location
                result = {
                    "success"           : False,
                    "file_location"     : f
                }
                self.result[f] = result
        self.complete = True

class VfParser(threading.Thread):

    def __init__(self, files):
        self.files          = files
        self.result         = {}
        self.complete       = False
        threading.Thread.__init__(self)

    def run(self):
        for f in self.files:
            parser_command = 'java -jar "{0}" "{1}"'.format(
                os.path.join(config.base_path,"bin","vf-parser.jar"),
                f)

            result_string = ""
            p = subprocess.Popen(parser_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            if p.stdout is not None : 
                for line in p.stdout.readlines():
                    result_string += line
            elif p.stderr is not None :
                print "****ERROR****"
                for line in p.stderr.readlines():
                    print line

            try:    
                self.result[f] = json.loads(result_string)
            except:
                #print "error on: ",self.file_location
                result = {
                    "success"           : False,
                    "file_location"     : f
                }
                self.result[f] = result
        self.complete = True
