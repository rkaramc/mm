import sys
import pprint
import subprocess
import pipes
import json
sys.path.append('../')

def get_arguments(operation, ui=False, html=False):
    args = {
        '-o'        : operation,
        '--html'    : html
    }
    args['-c'] = 'SUBLIME_TEXT_3'
  
    #ui_operations = ['edit_project', 'new_project', 'unit_test', 'deploy', 'execute_apex', 'upgrade_project', 'new_project_from_existing_directory', 'debug_log']
    #if operation in ui_operations:
    #    args['--ui'] = True

    arg_string = []
    for x in args.keys():
        if args[x] != None and args[x] != True and args[x] != False:
            arg_string.append(x + ' ' + args[x] + ' ')
        elif args[x] == True or args[x] == None:
            arg_string.append(x + ' ')
    stripped_string = ''.join(arg_string).strip()
    return stripped_string

payload = {
    "project_name"  : "bloat",
    "client"        : "SUBLIME_TEXT_3"
}

# payload = {
#     "username"      : "mm@force.com",
#     "password"      : "force",
#     "org_type"      : "developer"
# }   

# payload = {
#     "project_name"  : "bloat",
#     "username"      : "mm@force.com",
#     "password"      : "force",
#     "org_type"      : "developer"
# }   

# payload = {
#     "project_name"  : "bloat",
#     "username"      : "joeferraro4@force.com",
#     "password"      : "352198",
#     "org_type"      : "developer"
# }

payload = {
    "project_name"          : "bloat",
    "check_only"            : True,
    "rollback_on_error"     : True,
    "destinations"          : [
        {
            "username"  : "joeferraro4@force.com",
            "id"        : "SJKNL85Y497BZZXJEANLPS5B9SX61U4L",
            "org_type"  : "developer"
        }
    ],
    "package"               : {
        "ApexClass" : "*"
    },
    "rollback_on_error"     : True,
    "run_tests"             : False  
}

operation = 'deploy'

process = subprocess.Popen("{0} {1} {2}".format('/Users/josephferraro/Development/joey2/bin/python', pipes.quote('/Users/josephferraro/Development/Python/mavensmate/mm/mm.py'), get_arguments(operation)), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

if type(payload) is dict:
    payload = json.dumps(payload)  
#print(payload)  
try:
    process.stdin.write(payload)
except:
    process.stdin.write(payload.encode('utf-8'))
process.stdin.close()

if process.stdout is not None: 
    mm_response = process.stdout.readlines()
elif process.stderr is not None:
    mm_response = process.stderr.readlines()
try:
    response_body = '\n'.join(mm_response)
except:
    strs = []
    for line in mm_response:
        strs.append(line.decode('utf-8'))   
    response_body = '\n'.join(strs)

#print(response_body)
myjson = json.loads(response_body)
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(response_body)
