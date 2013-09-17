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
        self.multiple_form              = None
        self.see_all_data               = None
        self.without_sharing_count      = 0
        self.dml_for_loop_count         = 0
        self.soql_for_loop_count        = 0
        self.without_sharing_count      = 0
        self.negative_soql_count        = 0
        self.no_where_clause_count      = 0
        self.action_poller_count        = 0
        self.multiple_form_count        = 0
        self.see_all_data_count         = 0
        self.apex_files_to_check        = []
        self.vf_files_to_check          = []
        self.parser_results             = {}
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
                "action_poller" : {
                    "label"     : "Visualforce Pages using actionpoller",
                    "count"     : 0,
                    "results"   : []
                },
                "multiple_form" : {
                    "label"     : "Visualforce Pages with multiple forms",
                    "count"     : 0,
                    "results"   : []
                },
                "hardcoded_url" : {
                    "label"     : "Visualforce Pages with hardcoded URLs",
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

        parser_threads = []

        file_chunks = list(mm_util.grouper(8, self.apex_files_to_check))
        for files in file_chunks:                    
            thread = ApexParser(files)
            parser_threads.append(thread)
            thread.start()
            
        for thread in parser_threads:
            thread.join()
            if thread.complete:
                self.parser_results.update(thread.result)
        
        #pp = pprint.PrettyPrinter(indent=2)
        #pp.pprint(self.parser_results)

        for file_name in self.apex_files_to_check:
            parser_result = self.parser_results[file_name]

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
                if ' where ' not in lower_query:
                    no_where_clause_matches.append(query)
                if ' not like ' in lower_query or '!=' in lower_query:
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

        self.result["visualforce_statistics"]["action_poller"]["count"]     = self.action_poller_count
        self.result["visualforce_statistics"]["multiple_form"]["count"]     = self.multiple_form_count
        
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
