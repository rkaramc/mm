import os
import json
import re
import config
import shutil
import tempfile 
import string
import random
import base64
import zipfile
import time
import datetime
import threading
import sys
import xmltodict
import codecs
import traceback
import plistlib
import itertools
from StringIO import StringIO
if sys.platform == 'linux2':
    import gnomekeyring
else:
    import keyring
import urllib2
import webbrowser
from operator import itemgetter
from exceptions import MMException
from jinja2 import Environment, FileSystemLoader

import jinja2.ext
import jinja2htmlcompress
from jinja2htmlcompress import HTMLCompress

WSDL_PATH = os.path.join(config.base_path,"lib","wsdl") #this can be overridden by client settings or request parameter

TOOLING_API_EXTENSIONS = ['cls', 'trigger', 'page', 'component']

SFDC_API_VERSION = "28.0" #is overridden upon instantiation of mm_connection if plugin specifies mm_api_version

PRODUCTION_ENDPOINT_SHORT = "https://www.salesforce.com"
SANDBOX_ENDPOINT_SHORT    = "https://test.salesforce.com"
PRERELEASE_ENDPOINT_SHORT = "https://prerellogin.pre.salesforce.com"

PRODUCTION_ENDPOINT = "https://www.salesforce.com/services/Soap/u/"+str(SFDC_API_VERSION)
SANDBOX_ENDPOINT    = "https://test.salesforce.com/services/Soap/u/"+str(SFDC_API_VERSION)
PRERELEASE_ENDPOINT = "https://prerellogin.pre.salesforce.com/services/Soap/u/"+str(SFDC_API_VERSION)

ENDPOINTS = {
    "production" : PRODUCTION_ENDPOINT,
    "developer"  : PRODUCTION_ENDPOINT,
    "sandbox"    : SANDBOX_ENDPOINT,
    "prerelease" : PRERELEASE_ENDPOINT
}

URL_TO_ENDPOINT_TYPE = {
    PRODUCTION_ENDPOINT : "production",
    SANDBOX_ENDPOINT    : "sandbox",
    PRERELEASE_ENDPOINT : "prerelease"
}

template_path = os.path.join(config.base_path,"lib","templates")

env = Environment(loader=FileSystemLoader(template_path),trim_blocks=True)

def set_endpoints():
    global PRODUCTION_ENDPOINT
    global SANDBOX_ENDPOINT
    global PRERELEASE_ENDPOINT
    global ENDPOINTS
    PRODUCTION_ENDPOINT = "https://www.salesforce.com/services/Soap/u/"+str(SFDC_API_VERSION)
    SANDBOX_ENDPOINT    = "https://test.salesforce.com/services/Soap/u/"+str(SFDC_API_VERSION)
    PRERELEASE_ENDPOINT = "https://prerellogin.pre.salesforce.com/services/Soap/u/"+str(SFDC_API_VERSION)
    ENDPOINTS = {
        "production" : PRODUCTION_ENDPOINT,
        "developer"  : PRODUCTION_ENDPOINT,
        "sandbox"    : SANDBOX_ENDPOINT,
        "prerelease" : PRERELEASE_ENDPOINT
    }

def get_soap_url_from_custom_url(custom_url):
    if "Soap" in custom_url:
        return custom_url
    else:
        if custom_url.endswith("/"):
            return custom_url+"services/Soap/u/"+str(SFDC_API_VERSION)
        else:
            return custom_url+"/services/Soap/u/"+str(SFDC_API_VERSION)

def get_timestamp():
    ts = time.time()
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H:%M:%S')

def parse_json_from_file(location):
    if not os.path.exists(location):
        return {}
    try:
        json_data = open(location)
        if json_data:
            data = json.load(json_data)
            json_data.close()
            return data
    except:
        return parse_json(location)

def parse_xml_from_file(location):
    if not os.path.exists(location):
        return {}
    try:
        xml_data = open(location)
        data = xmltodict.parse(xml_data,postprocessor=xmltodict_postprocessor)
        xml_data.close()
        return data
    except:
        return {}

def get_iso_8601_timestamp(delta_in_minutes=None):
    now = datetime.datetime.now()
    if delta_in_minutes == None:
        return now.isoformat()
    else:
        delta = datetime.timedelta(minutes = delta_in_minutes)
        expiration_date = now + delta
        return expiration_date.isoformat()

def get_sfdc_endpoint(url):
    endpoint = PRODUCTION_ENDPOINT
    if "test" in url:
        endpoint = SANDBOX_ENDPOINT
    elif "prerellogin.pre.salesforce.com" in url:
        endpoint = PRERELEASE_ENDPOINT
    return endpoint

def get_sfdc_endpoint_by_type(type):
    if type in ENDPOINTS: 
        return ENDPOINTS[type] 
    else: 
        return ""

def is_directory_empty(path):
    for f in os.listdir(path):
        if not f.startswith('.'):
            return False
    return True

def put_project_directory_on_disk(project_name, **kwargs):
    if 'force' in kwargs and kwargs['force'] == True:
        if os.path.isdir(os.path.join(config.connection.workspace,project_name)):
            shutil.rmtree(os.path.join(config.connection.workspace,project_name))
    os.makedirs(os.path.join(config.connection.workspace,project_name))

def put_password_by_key(key, password):
    if sys.platform == 'linux2':
        try:
            gnomekeyring.set_network_password_sync(None, key, 'MavensMate: '+key,
                None, None, None, None, 0, password)
        except gnomekeyring.CancelledError:
            raise MMException('Unable to set password')
    else:
        keyring.set_password('MavensMate: '+key, key, password)

def get_password_by_key(key):
    if sys.platform == 'linux2':
        try:
            items = gnomekeyring.find_network_password_sync(key, 'MavensMate: '+key)
            return items[0]['password']
        except gnomekeyring.CancelledError:
            raise MMException('Unable to retrieve password')
    else:
        return keyring.get_password('MavensMate: '+key, key)

def delete_password_by_key(key):
    try:
        return keyring.delete_password('MavensMate: '+key, key)
    except:
        #TODO: this has not been implemented in keyring yet :-(
        pass

def get_file_extension(path):
    return os.path.splitext(path)[1]

def get_file_as_string(file_path):
    try:
        f = codecs.open(file_path, "r", "utf8")
        file_body = f.read()
        f.close()
        return file_body
    except Exception, e:
        print "Couldn't open "+str(file_path)+" because: "+e.message
    return ""

def parse_rest_response(body):
    rjson = json.loads(body)
    return rjson

def zip_directory(directory_to_zip, where_to_put_zip_file=None, base64_encode=True):
    if where_to_put_zip_file == None:
        where_to_put_zip_file = get_temp_directory()
    shutil.make_archive(os.path.join(where_to_put_zip_file,'mm'), 'zip', os.path.join(directory_to_zip))
    if base64_encode == True:
        file_contents = open(os.path.join(where_to_put_zip_file,"mm.zip"), "rb").read()
        base64_zip = base64.b64encode(file_contents)
        return base64_zip

def extract_base64_encoded_zip(encoded, where_to_extract):
    zip_path = os.path.join(where_to_extract,"metadata.zip")
    #write file to disk
    data = base64.b64decode(encoded)
    src = open(zip_path, "wb")
    src.write(data)
    src.close()
    #extract file from disk - z.extractall(where_to_extract) fails with non ascii chars
    f = zipfile.ZipFile(zip_path, 'r')
    for fileinfo in f.infolist():
        path = where_to_extract
        directories = fileinfo.filename.decode('utf8').split('/')
        for directory in directories:
            path = os.path.join(path, directory)
            if directory == directories[-1]: break # the file
            if not os.path.exists(path):
                os.makedirs(path)
        outputfile = open(path, "wb")
        shutil.copyfileobj(f.open(fileinfo.filename), outputfile)
    #remove zip file
    try:
        os.remove(where_to_extract+"/metadata.zip")
    except:
        pass #windows may not like this, so we'll verify the cleanup later

def rename_directory(old_directory_name, new_directory_name):
    os.rename(old_directory_name, new_directory_name)

def xmltodict_postprocessor(path, key, value):
    try:
        if value == 'true':
            return key, True
        elif value == 'false':
            return key, False
        else:
            return key, value
    except (ValueError, TypeError):
        return key, value
        # >>> xmltodict.parse('<a><b>1</b><b>2</b><b>x</b></a>',
        # ...                 postprocessor=postprocessor)
        # OrderedDict([(u'a', OrderedDict([(u'b:int', [1, 2]), (u'b', u'x')]))])

def parse_json(filename):
    """ Parse a JSON file
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """
    # Regular expression for comments
    comment_re = re.compile(
        '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
        re.DOTALL | re.MULTILINE
    )

    with open(filename) as f:
        content = ''.join(f.readlines())

        ## Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)

        # Return json file
        return json.loads(content)

def get_temp_directory():
    if 'linux' in sys.platform:
        if not os.path.exists(os.path.join(os.path.expanduser('~'),".mm")):
            os.makedirs(os.path.join(os.path.expanduser('~'),".mm"))
        return os.path.join(os.path.expanduser('~'),".mm")
    else:
        return tempfile.gettempdir()

def put_tmp_directory_on_disk(put_unpackaged_directory=False):
    tmp_dir = get_temp_directory()
    mm_tmp_directory = os.path.join(tmp_dir,".org.mavens.mavensmate."+get_random_string())
    os.makedirs(mm_tmp_directory)
    if put_unpackaged_directory == True:
        os.makedirs(os.path.join(mm_tmp_directory,"unpackaged"))
        return mm_tmp_directory, os.path.join(mm_tmp_directory,"unpackaged")
    return mm_tmp_directory

def put_tmp_file_on_disk(name, body, ext=''):
    tmp_dir = get_temp_directory()
    file_name = '[--SERVER COPY--] '+name
    f = open("{0}/{1}.{2}".format(tmp_dir, file_name, ext), 'w')
    f.write(body)
    f.close()
    return "{0}/{1}.{2}".format(tmp_dir, file_name, ext)

def put_file_in_tmp_directory(file_name, body):
    tmp_dir = get_temp_directory()
    f = open(os.path.join(tmp_dir, file_name), 'w')
    f.write(body)
    f.close()
    return os.path.join(tmp_dir, file_name)

def put_package_xml_in_directory(directory, file_contents, isDelete=False):
    file_name = 'package.xml' if isDelete == False else 'destructiveChanges.xml'
    f = open("{0}/{1}".format(directory, file_name), 'w')
    f.write(file_contents)
    f.close()

def put_empty_package_xml_in_directory(directory, file_contents):
    file_name = 'package.xml'
    f = open("{0}/{1}".format(directory, file_name), 'w')
    f.write(file_contents)
    f.close()

def get_random_string(size=8, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def new_mavensmate_id(size=32, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for x in range(size))

def delete_directory(directory):
    if os.path.isdir(directory):
        shutil.rmtree(directory)

#returns package.xml contents based on dict of metadata
def get_package_xml_contents(metadata_hash={}):
    #metadata_hash = {'ApexClass':['foo', 'bar'], 'ApexPage':'*'}
    #metadata_hash = {'ApexClass':'*'}
    template = env.get_template('package.html')
    return template.render(sfdc_api_version=SFDC_API_VERSION, hash=metadata_hash)

def get_empty_package_xml_contents():
    template = env.get_template('empty_package.html')
    return template.render(sfdc_api_version=SFDC_API_VERSION)

def get_default_metadata_data():
    return parse_json_from_file(config.base_path + "/lib/sforce/metadata/default_metadata.json")
    
def get_child_metadata_data():
    return parse_json_from_file(config.base_path + "/lib/sforce/metadata/default_child_metadata.json")

def get_meta_type_by_suffix(suffix):
    try:
        if '-meta' in suffix:
            suffix = suffix.split('-meta')[0]
        data = get_default_metadata_data()
        if '.' in suffix:
            suffix = suffix.replace('.','')
        for item in data["metadataObjects"]: 
            if 'suffix' in item and item['suffix'] == suffix:
                return item
        if config.describe_data != None:
            project_org_describe = config.describe_data
        if config.project != None and os.path.isfile(os.path.join(config.project.location,'config','.describe')):
            project_org_describe = parse_json_from_file(os.path.join(config.project.location,'config','.describe'))
        if project_org_describe != None and 'metadataObjects' in project_org_describe:
            for item in project_org_describe["metadataObjects"]: 
                if 'suffix' in item and item['suffix'] == suffix:
                    return item
    except:
        return None

def get_meta_type_by_dir(dir_name):
    parent_data = get_default_metadata_data()
    child_data = get_child_metadata_data()
    data = parent_data['metadataObjects'] + child_data
    for item in data: 
        if 'directoryName' in item and item['directoryName'].lower() == dir_name.lower():
            return item
        elif 'tagName' in item and item['tagName'].lower() == dir_name.lower():
            return item
    '''
        > quick and dirty fix for users experiencing issues with "newer" metadata types not properly tested by mm
        > if the project has a cached .describe, let's use that to detect metadata types
    '''
    try:
        if config.describe_data != None:
            project_org_describe = config.describe_data
        if config.project != None and os.path.isfile(os.path.join(config.project.location,'config','.describe')):
            project_org_describe = parse_json_from_file(os.path.join(config.project.location,'config','.describe'))
        if project_org_describe != None and 'metadataObjects' in project_org_describe:
            for item in project_org_describe["metadataObjects"]: 
                if 'directoryName' in item and item['directoryName'].lower() == dir_name.lower():
                    return item
                elif 'tagName' in item and item['tagName'].lower() == dir_name.lower():
                    return item
    except:
        pass

def get_meta_type_by_name(name):
    data = get_default_metadata_data()
    child_data = get_child_metadata_data()
    for item in data["metadataObjects"]: 
        if 'xmlName' in item and item['xmlName'] == name:
            return item 
    for item in child_data: 
        if 'xmlName' in item and item['xmlName'] == name:
            return item
    '''
        > quick and dirty fix for users experiencing issues with "newer" metadata types not properly tested by mm
        > if the project has a cached .describe, let's use that to detect metadata types
    '''
    try:
        if config.describe_data != None:
            project_org_describe = config.describe_data
        if config.project != None and os.path.isfile(os.path.join(config.project.location,'config','.describe')):
            project_org_describe = parse_json_from_file(os.path.join(config.project.location,'config','.describe'))
        if project_org_describe != None and 'metadataObjects' in project_org_describe:
            for item in project_org_describe["metadataObjects"]: 
                if 'xmlName' in item and item['xmlName'] == name:
                    return item
    except:
        pass
    #raise MMException('Unknown metadata type: '+name)

def put_skeleton_files_on_disk(metadata_type, where, github_template=None, params={}):
    """
        Generates file based on jinja2 templates
    """
    api_name = params["api_name"]
    file_name = github_template["file_name"]
    template_source = config.connection.get_plugin_client_setting('mm_template_source', 'joeferraro/MavensMate-Templates/master')
    template_location = config.connection.get_plugin_client_setting('mm_template_location', 'remote')

    try:
        if template_location == 'remote':
            if 'linux' in sys.platform:
                template_body = os.popen("wget https://raw.github.com/{0}/{1}/{2} -q -O -".format(template_source, metadata_type, file_name)).read()
            else:
                template_body = urllib2.urlopen("https://raw.github.com/{0}/{1}/{2}".format(template_source, metadata_type, file_name)).read()
        else:
            template_body = get_file_as_string(os.path.join(template_source,metadata_type,file_name))
    except:
        template_body = get_file_as_string(os.path.join(config.base_path,"lib","templates","github-local",metadata_type,file_name))
    
    template = env.from_string(template_body)
    file_body = template.render(params)
    metadata_type = get_meta_type_by_name(metadata_type)
    os.makedirs("{0}/{1}".format(where, metadata_type['directoryName']))
    f = open("{0}/{1}/{2}".format(where, metadata_type['directoryName'], api_name+"."+metadata_type['suffix']), 'w')
    f.write(file_body)
    f.close()

    template = env.get_template('meta.html')
    file_body = template.render(api_name=api_name, sfdc_api_version=SFDC_API_VERSION,meta_type=metadata_type['xmlName'])
    f = open("{0}/{1}/{2}".format(where, metadata_type['directoryName'], api_name+"."+metadata_type['suffix'])+"-meta.xml", 'w')
    f.write(file_body)
    f.close()

def parse_manifest(location):
    return parse_json_from_file(location)

def base_local_server_url():
    port = config.connection.get_plugin_client_setting('mm_server_port', 9876)
    return 'http://127.0.0.1:{0}'.format(port)

def platform():
    if sys.platform == 'win32':
        return 'windows'
    elif 'linux' in sys.platform:
        return 'linux'
    elif 'darwin' in sys.platform:
        return 'osx'
    else:
        return 'osx'

def base_path_normal():
    if sys.platform == 'win32':
        return config.base_path.replace('\\', '/')
    else:
        return config.base_path

def generate_ui(operation,params={}):
    template_path = config.base_path + "/lib/ui/templates"
    env = Environment(loader=FileSystemLoader(template_path),trim_blocks=True)
    env.globals['platform']                 = platform
    env.globals['play_sounds']              = play_sounds
    env.globals['project_settings']         = project_settings
    env.globals['metadata_types']           = metadata_types
    env.globals['client_subscription_list'] = client_subscription_list
    env.globals['base_local_server_url']    = base_local_server_url
    env.globals['operation']                = operation
    env.globals['project_location']         = config.project.location
    env.globals['base_path_normal']         = base_path_normal
    temp = tempfile.NamedTemporaryFile(delete=False, prefix="mm", suffix=".html")
    if operation == 'new_project':
        template = env.get_template('/project/new.html')
        file_body = template.render(
            user_action='new',
            workspace=config.connection.workspace,
            client=config.connection.plugin_client,
            workspaces=config.connection.get_workspaces()
            ).encode('UTF-8')
    elif operation == 'checkout_project':
        template = env.get_template('/project/new.html')
        file_body = template.render(user_action='checkout',workspace=config.connection.workspace,client=config.connection.plugin_client).encode('UTF-8')
    elif operation == 'upgrade_project':
        template = env.get_template('/project/upgrade.html')
        creds = config.project.get_creds()
        org_url = creds.get('org_url', None)
        if org_url == None:
            org_url = ''
        file_body = template.render(
            name=config.project.project_name,
            project_location=config.project.location,
            client=config.connection.plugin_client,
            username=creds['username'],
            org_type=creds['org_type'],
            org_url=org_url,
            workspace=config.connection.workspace
        ).encode('UTF-8')
    elif operation == 'edit_project':
        template = env.get_template('/project/edit.html')
        creds = config.project.get_creds()
        org_url = creds.get('org_url', None)
        if org_url == None:
            org_url = ''
        file_body = template.render(
            name=config.project.project_name,
            username=creds['username'],
            password=creds['password'],
            org_type=creds['org_type'],
            org_url=org_url,
            has_indexed_metadata=config.project.is_metadata_indexed,
            project_location=config.project.location,
            client=config.connection.plugin_client
        ).encode('UTF-8')
    elif operation == 'unit_test':
        if int(float(SFDC_API_VERSION)) < 29 or config.connection.get_plugin_client_setting("mm_use_legacy_test_ui", False):
            template = env.get_template('/unit_test/index28.html')
        else:
            template = env.get_template('/unit_test/index.html')
            
        istest = re.compile(r"@istest", re.I)
        testmethod = re.compile(r"testmethod", re.I)

        apex_classes = []
        for dirname, dirnames, filenames in os.walk(config.project.location+"/src/classes"):
            for f in filenames:
                if f == "." or f == ".." or '-meta.xml' in f or ".svn" in f:
                    continue
                try:
                    full_file_path = os.path.join(dirname,f)
                    if istest.search(open(full_file_path).read()) or testmethod.search(open(full_file_path).read()):
                        apex_classes.append(f.split(".")[0])
                except:
                    continue
        if "selected" in params:
            selected = params["selected"]
        else:
            selected = []
        file_body = template.render(
            name=config.project.project_name,
            classes=apex_classes,
            selected=selected,
            client=config.connection.plugin_client).encode('UTF-8')
    elif operation == 'deploy':
        compare = config.connection.get_plugin_client_setting("mm_compare_before_deployment", True)
        template = env.get_template('/deploy/index.html')
        file_body = template.render(
            name=config.project.project_name,
            has_indexed_metadata=config.project.is_metadata_indexed,
            project_location=config.project.location,
            connections=config.project.get_org_connections(),
            operation=operation,
            compare=compare,
            deployments=config.project.get_deployments(),
            client=config.connection.plugin_client).encode('UTF-8')
    elif operation == 'execute_apex':
        template = env.get_template('/execute_apex/index.html')
        file_body = template.render(
            name=config.project.project_name,
            project_location=config.project.location,
            client=config.connection.plugin_client).encode('UTF-8')
    elif operation == 'new_project_from_existing_directory':
        project_name = os.path.basename(params['directory'])
        template = env.get_template('/project/new_from_existing.html')
        file_body = template.render(
            project_name=project_name,
            directory=params['directory'],
            workspaces=config.connection.get_workspaces(),
            client=config.connection.plugin_client).encode('UTF-8')
    elif operation == 'debug_log':
        template = env.get_template('/debug_log/index.html')
        file_body = template.render(
            project_name=config.project.project_name,
            users=config.project.get_org_users_list(),
            user_id=config.sfdc_client.user_id,
            apex_items=config.sfdc_client.get_apex_classes_and_triggers(),
            #logs=config.project.get_org_logs(),
            client=config.connection.plugin_client).encode('UTF-8')
    elif operation == 'github':
        template = env.get_template('/github/index.html')
        file_body = template.render(
            client=config.connection.plugin_client).encode('UTF-8')
    elif operation == 'project_health_check':
        template = env.get_template('/project/health_check.html')
        file_body = template.render(
            client=config.connection.plugin_client,
            name=config.project.project_name
            ).encode('UTF-8')
    else:
        raise MMException('Unsupported UI Command')
    temp.write(file_body)
    temp.close()
    return temp.name

def run_as_daemon(func):
    th = threading.Thread(target=func)
    th.daemon = True
    th.start()

def calculate_coverage(result, id_to_name_map):
    coverage = {}
    for r in result["records"]:
        if r["ApexClassOrTriggerId"].startswith('01q'):
            r["ApexClassOrTrigger"] = "ApexTrigger"
        elif r["ApexClassOrTriggerId"].startswith('01p'):
            r["ApexClassOrTrigger"] = "ApexClass"
        r["ApexClassOrTriggerName"] = id_to_name_map[r["ApexClassOrTriggerId"]]
        key = r["ApexClassOrTrigger"]+r["ApexClassOrTriggerName"] 
        if key not in coverage:
            coverage[key] = r #ApexClass01pxyz123 : { coverage }
        else:
            existing_covered_lines = coverage[key]["Coverage"]["coveredLines"]
            this_class_covered_lines = r["Coverage"]["coveredLines"]
            new_covered_lines = list(set(existing_covered_lines) | set(this_class_covered_lines))  
            coverage[key]["Coverage"]["coveredLines"] = new_covered_lines

            existing_uncovered_lines = coverage[key]["Coverage"]["uncoveredLines"]
            this_class_uncovered_lines = r["Coverage"]["uncoveredLines"]
            new_covered_lines = list(set(existing_uncovered_lines) | set(this_class_uncovered_lines))  
            coverage[key]["Coverage"]["uncoveredLines"] = new_covered_lines

            new_uncovered = []
            for uncovered_line in coverage[key]["Coverage"]["uncoveredLines"]:
                if uncovered_line not in coverage[key]["Coverage"]["coveredLines"]:
                    new_uncovered.append(uncovered_line)

            coverage[key]["Coverage"]["uncoveredLines"] = new_uncovered

    return_coverage = []
    for key, value in coverage.iteritems():
        return_coverage.append(coverage[key])
    return return_coverage

def generate_html_response(operation, obj, params=None):
    template_path = config.base_path + "/lib/ui/templates"
    env = Environment(loader=FileSystemLoader(template_path),trim_blocks=True,extensions=['jinja2.ext.loopcontrols', jinja2htmlcompress.HTMLCompress])
    env.globals['get_file_lines'] = get_file_lines
    env.globals['htmlize'] = htmlize
    env.globals['does_file_exist'] = does_file_exist
    if operation == 'test_legacy':
        template = env.get_template('/unit_test/result.html')
        config.logger.debug(json.dumps(obj, sort_keys=True,indent=4))
        result = process_unit_test_result(obj)
        config.logger.debug('\n\n\n\n\n')
        config.logger.debug(json.dumps(result, sort_keys=True,indent=4))
        html = template.render(result=result,results_normal={},args=params)
    elif operation == 'unit_test' or operation == 'test':
        if int(float(SFDC_API_VERSION)) < 29 or config.connection.get_plugin_client_setting("mm_use_legacy_test_ui", False):
            template = env.get_template('/unit_test/result28.html')
        else:
            template = env.get_template('/unit_test/result.html')
        config.logger.debug(json.dumps(obj, sort_keys=True,indent=4))
        result = process_unit_test_result(obj)
        config.logger.debug('\n\n\n\n\n')
        config.logger.debug(json.dumps(result, sort_keys=True,indent=4))
        html = template.render(result=result,results_normal={},args=params)
    elif operation == 'deploy':
        template = env.get_template('/deploy/result.html')
        deploy_results = []
        for result in obj:
            if 'details' in result: #metadata api v29 and above
                #if 'componentFailures' in result['details']:
                if 'runTestResult' in result['details'] and 'codeCoverage' in result['details']['runTestResult']:
                    result['parsedTestResults'] = process_unit_test_result(result['details']['runTestResult'])
                    deploy_results.append(result)
                else:
                    deploy_results.append(result)
            elif 'messages' in result:
                for m in result['messages']:
                    if m['success'] == False:
                        result['success'] = False
                        break
            if 'runTestResult' in result and 'codeCoverage' in result['runTestResult']:
                result['parsedTestResults'] = process_unit_test_result(result['runTestResult'])
                deploy_results.append(result)
            else:
                deploy_results.append(result)
        config.logger.debug(obj)
        config.logger.debug(deploy_results)
        html = template.render(deploy_results=deploy_results,args=params)
    elif operation == 'deploy_compare':
        template = env.get_template('/deploy/compare_result.html')
        html = template.render(compare_result=obj,args=params)
    elif operation == 'project_health_check':
        template = env.get_template('/snippets/health_check_result.html')
        html = template.render(result=obj)
    return html

def play_sounds():
    return config.connection.get_plugin_client_setting('mm_play_sounds', False)

def project_settings():
    try:
        return config.project.settings
    except:
        return {}

def client_subscription_list():
    try:
        return config.connection.get_plugin_client_setting('mm_default_subscription')
    except:
        return []

def metadata_types():
    try:
        if config.describe_data != None and 'metadataObjects' in config.describe_data:
            return sorted(config.describe_data["metadataObjects"], key=itemgetter('xmlName'))
        elif config.project != None and os.path.isfile(os.path.join(config.project.location,'config','.describe')):
            project_org_describe = parse_json_from_file(os.path.join(config.project.location,'config','.describe'))
            return sorted(project_org_describe["metadataObjects"], key=itemgetter('xmlName'))
        else:
            return sorted(get_default_metadata_data()["metadataObjects"], key=itemgetter('xmlName'))
    except:
        return sorted(get_default_metadata_data()["metadataObjects"], key=itemgetter('xmlName'))

def does_file_exist(api_name, metadata_type_name):
    metadata_type = get_meta_type_by_name(metadata_type_name)
    if os.path.isfile(os.path.join(config.project.location,"src",metadata_type['directoryName'],api_name+"."+metadata_type['suffix'])):
        return True
    else:
        return False

def get_file_lines(api_name, metadata_type_name):
    try:
        metadata_type = get_meta_type_by_name(metadata_type_name)
        if os.path.isfile(os.path.join(config.project.location,"src",metadata_type['directoryName'],api_name+"."+metadata_type['suffix'])):
            return open(os.path.join(config.project.location,"src",metadata_type['directoryName'],api_name+"."+metadata_type['suffix'])).readlines()
        else:
            return []
    except:
        return []

def is_project_legacy():
    if not os.path.exists(os.path.join(config.project.location,"config",".debug")):
        return True
    if os.path.exists(os.path.join(config.project.location,"config","settings.yaml")):
        return True
    elif os.path.exists(os.path.join(config.project.location,"config",".settings")):
        current_settings = parse_json_from_file(os.path.join(config.project.location,"config",".settings"))
        if 'subscription' not in current_settings or 'workspace' not in current_settings:
            return True
        else:
            return False
    else:
        return False

def htmlize(seed):
    try:
        seed = seed.decode('utf8')
        seed = re.sub("&", "&amp;", seed)
        seed = re.sub('"', "&quot;", seed)
        seed = re.sub("<", "&lt;", seed)
        seed = re.sub(">", "&gt;", seed)
        seed = re.sub("\t", "&nbsp;&nbsp;&nbsp;&nbsp;", seed)
        seed = re.sub(" ", "&nbsp;", seed)
        seed = re.sub("\n", "<br/>", seed)
        return seed
    except:
        return 'Not Available'

def launch_ui(tmp_html_file_location):
    use_browser_as_ui = config.connection.get_plugin_client_setting('mm_use_browser_as_ui', False)
    if use_browser_as_ui or sys.platform != 'darwin':
        if 'linux' in sys.platform:
            #webbrowser.open("{0}{1}".format("file:///",tmp_html_file_location))
            b = lambda : webbrowser.open("{0}{1}".format("file:///",tmp_html_file_location))
            threading.Thread(target=b).start()
        elif 'darwin' in sys.platform:
            webbrowser.open("{0}{1}".format("file:///",tmp_html_file_location))
        else: 
            webbrowser.get('windows-default').open("{0}{1}".format("file:///",tmp_html_file_location))
    else:
        os.system("open -n '"+config.base_path+"/bin/MavensMateWindowServer.app' --args -url '"+tmp_html_file_location+"'")
    time.sleep(1)
    #threading.Thread(target=remove_tmp_html_file, args=(tmp_html_file_location,)).start()

def remove_tmp_html_file(tmp_html_file_location):
    time.sleep(1)
    os.remove(tmp_html_file_location)

def generate_response(obj):
    return json.dumps(obj)

def generate_success_response(message, type="text"):
    res = {
        "time"      : repr(time.time() - config.mm_start),
        "success"   : True,
        "body_type" : type,
        "body"      : message
    }
    return json.dumps(res)

def generate_request_for_action_response(message, operation, actions=[], **kwargs):
    res = {
        "success"       : False,
        "body_type"     : "text",
        "body"          : message,
        "actions"       : actions,
        "operation"     : operation
    }
    if 'tmp_file_path' in kwargs and kwargs['tmp_file_path'] != None:
        res['tmp_file_path'] = kwargs['tmp_file_path']
    return json.dumps(res)

def generate_error_response(message, dump_to_json=True, verbose=False):
    try:
        stack_trace = ''
        trace = format_exception()
        message = message.strip()
        if message == None or message == '':
            message = 'An error has occurred. Please enable plugin logging, retry your operation and paste any relevant log(s) to a new GitHub issue.'
        if trace != None and trace != 'None' and 'MMException' not in trace and (config.connection.verbose or verbose):
            # if message = e.message just use the trace
            if len(trace):
                stack_trace += trace
            stack_trace += '\n'+'[ENVIRONMENT]: '
            # get OS info
            try:
                if sys.platform == 'darwin':
                    # try:
                    #     release, versioninfo, machine = platform.mac_ver()
                    #     stack_trace += 'MacOS ' + release
                    # except:
                    #     stack_trace += 'MacOS '
                    pass
                #todo: support windows and linux
            except:
                pass
            # try to get the executable version
            try:
                if sys.platform == 'darwin':
                    dic = plistlib.readPlist('/Applications/MavensMate.app/Contents/Info.plist')
                    if 'CFBundleVersion' in dic:
                        stack_trace += ', MavensMate ' + dic['CFBundleVersion']
            except:
                pass

        if 'nodename nor servname provided' in stack_trace:
            message = 'No internet connection'

        config.logger.exception("[MAVENSMATE CAUGHT ERROR]")
        config.logger.debug(stack_trace)
        if config.connection.verbose or verbose:
            res = {
                "success"       : False,
                "body_type"     : "text",
                "body"          : message,
                "stack_trace"   : stack_trace
            }
        else:
            res = {
                "success"       : False,
                "body_type"     : "text",
                "body"          : message
            }
        if dump_to_json:
            return json.dumps(res)
        else:
            return res
    except:
        res = {
            "success"       : False,
            "body_type"     : "text",
            "body"          : message,
            "stack_trace"   : stack_trace
        }
        if dump_to_json:
            return json.dumps(res)
        else:
            return res

def format_exception(exc_info=None):
    if exc_info is None:
        exc_info = sys.exc_info()
    out = StringIO()
    traceback.print_exception(*exc_info, **dict(file=out))
    return out.getvalue()

def prepare_for_metadata_tree(metadata_list):
    apex_types = ['ApexClass', 'ApexComponent', 'ApexTrigger', 'ApexPage', 'StaticResource']
    for mt in metadata_list:
        mt['text']          = mt['xmlName']
        mt['title']         = mt['xmlName']
        mt['key']           = mt['xmlName']
        mt['folder']        = True
        mt['checked']       = True if mt['xmlName'] in apex_types else False
        mt['select']        = True if mt['xmlName'] in apex_types else False
        mt['children']      = []
        mt['cls']           = "folder"
        mt['isLazy']        = True
        mt['children']      = []
        mt['isFolder']      = True
        # mt['type']          = mt
        mt['level']         = 1
        mt['id']            = mt['xmlName']
        #mt["inFolder"]      = mt['inFolder'],
        mt["hasChildTypes"] = 'childXmlNames' in mt
    return metadata_list

def lower_keys(x):
    if isinstance(x, list):
        return [lower_keys(v) for v in x]
    if isinstance(x, dict):
        return dict((k.lower(), lower_keys(v)) for k, v in x.iteritems())
    return x

#prepares the unit test result for processing by the jinja template
def process_unit_test_result(result):
    
    config.logger.debug('>>>> RUN TEST RESULT')
    config.logger.debug(result)

    triggers = []
    classes = []

    if 'codeCoverage' in result:
        # for single results we don't get a list back
        if type(result['codeCoverage']) is not list:
            result['codeCoverage'] = [result['codeCoverage']]
        for coverage_result in result['codeCoverage']:
            if 'locationsNotCovered' in coverage_result and type(coverage_result['locationsNotCovered']) is not list:
                coverage_result['locationsNotCovered'] = [coverage_result['locationsNotCovered']]
            if 'numLocations' in coverage_result and 'numLocationsNotCovered' in coverage_result:
                locations = int(float(coverage_result['numLocations']))
                locations_not_covered = int(float(coverage_result['numLocationsNotCovered']))
                percent_covered = 0 
                if locations > 0:
                    percent_covered = int(round(100 * ((float(locations) - float(locations_not_covered)) / locations)))
                coverage_result['percentCovered'] = percent_covered
                if percent_covered < 40:
                    coverage_result['coverageLevel'] = 'danger'
                elif percent_covered >= 40 and percent_covered < 75:
                    coverage_result['coverageLevel'] = 'warning'
                elif percent_covered >= 75:
                    coverage_result['coverageLevel'] = 'success'
                else:
                    coverage_result['coverageLevel'] = 'info'

            if 'type' in coverage_result:
                if coverage_result['type'] == 'Trigger':
                    triggers.append(coverage_result)
                else:
                    classes.append(coverage_result)
            elif 'id' in coverage_result:
                result_id = coverage_result['id']
                if result_id.startswith('01q'):
                    triggers.append(coverage_result)
                else:
                    classes.append(coverage_result)

    if 'codeCoverageWarnings' in result:
        # for single results we don't get a list back
        if type(result['codeCoverageWarnings']) is not list:
            result['codeCoverageWarnings'] = [result['codeCoverageWarnings']]
        for warning in result['codeCoverageWarnings']:
            if 'name' in warning and type(warning['name']) is not str and type(warning['name']) is not unicode:
               warning['name'] = None 

    results_normal = {}
    #{"foo"=>[{:name = "foobar"}{:name = "something else"}], "bar"=>[]}
    pass_fail = {}
    if 'successes' in result:
        # for single results we don't get a list back
        if type(result['successes']) is not list:
            result['successes'] = [result['successes']]
        for success in result['successes']:
            if success['name'] not in pass_fail:
                pass_fail[success['name']] = {
                    'fail': 0,
                    'pass': 1
                }
            else:
                pass_fail[success['name']]['pass'] += 1
            if success['name'] not in results_normal: #key isn't there yet, put it in        
                results_normal[success['name']] = [success]
            else: #key is there, let's add metadata to it
                arr = results_normal[success['name']] #get the existing array
                arr.append(success) #add the new piece of metadata
                results_normal[success['name']] = arr #replace the key
    
    if 'failures' in result:
        # for single results we don't get a list back
        if type(result['failures']) is not list:
            result['failures'] = [result['failures']]
        for failure in result['failures']:
            if failure['name'] not in pass_fail:
                pass_fail[failure['name']] = {
                    'fail': 1,
                    'pass': 0
                }
            else:
                pass_fail[failure['name']]['fail'] += 1
            if failure['name'] not in results_normal: #key isn't there yet, put it in        
                results_normal[failure['name']] = [failure]
            else: #key is there, let's add metadata to it
                arr = results_normal[failure['name']] #get the existing array
                arr.append(failure) #add the new piece of metadata
                results_normal[failure['name']] = arr #replace the key

    result['pass_fail'] = pass_fail

    result['results_normal'] = results_normal

    result['codeCoverage'] = {
        "triggers" : triggers,
        "classes" : classes
    }
    return result

def get_file_extension_no_period(path):
    name, ext = os.path.splitext(path)
    return ext.replace(".", "")

def get_file_name_no_extension(path):
    base=os.path.basename(path)
    return os.path.splitext(base)[0]

#returns metadata hash of selected files  #=> {"ApexClass" => ["aclass", "anotherclass"], "ApexTrigger" => ["atrigger", "anothertrigger"]}
def get_metadata_hash(selected_files=[]):
    meta_hash = {}
    for f in selected_files:
        if '-meta.xml' in f:
            continue
        name, ext = os.path.splitext(f)
        ext_no_period = ext.replace(".", "")   
        if os.path.basename(f).count('.') > 1: #fix for weird metadata types like approvalprocess
            base_name_no_ext = os.path.basename(f).split(".")[0]+"."+os.path.basename(f).split(".")[1]
        else:
            base_name_no_ext = os.path.basename(f).split(".")[0]
        try:
            metadata_definition = get_meta_type_by_suffix(ext_no_period)      
            meta_type = metadata_definition["xmlName"]
        except:
            if sys.platform == "win32":
                dir_parts = f.split("\\")
            else:
                dir_parts = f.split("/")
            if 'documents' in dir_parts:
                metadata_definition = get_meta_type_by_name("Document") 
                meta_type = metadata_definition["xmlName"]

        if meta_type not in meta_hash: #key isn't there yet, put it in        
            if metadata_definition['inFolder']:
                arr = f.split("/")
                if arr[len(arr)-2] != metadata_definition['directoryName']:
                    meta_hash[meta_type] = [arr[len(arr)-2]+"/"+base_name_no_ext] #file name with no extension
                else:
                    meta_hash[meta_type] = [base_name_no_ext]
            else:
                meta_hash[meta_type] = [base_name_no_ext]
        else: #key is there, let's add metadata to it
            meta_array = meta_hash[meta_type] #get the existing array
            if metadata_definition['inFolder']:
                arr = f.split("/")
                if arr[len(arr)-2] != metadata_definition['directoryName']:
                    meta_array.append(arr[len(arr)-2]+"/"+base_name_no_ext) #file name with no extension
                else:
                    meta_array.append(base_name_no_ext) #add the new piece of metadata
            else:
                meta_array.append(base_name_no_ext) #file name with no extension
            
            meta_hash[meta_type] = meta_array #replace the key
        
    return meta_hash
 
def parse_deploy_result(res):  
    return_result = {
        "id"        : res["id"],
        "success"   : res["success"]
    }
    messages        = parse_deploy_messages(res)
    retrieve_result = {}
    run_test_result = {}

   
    if 'runTestResult' in res and type(res['runTestResult']) is not list:
        return_result['runTestResult'] = [res['runTestResult']]
    else:
        return_result['runTestResult'] = res['runTestResult']    
    return return_result

def parse_deploy_messages(res):
    messages = []
    return_messages = []
    if 'messages' in res and type(res['messages']) is not list:
        messages = [res['messages']]
    else:
        messages = res['messages']
    for m in messages:
        return_messages.append({
            "changed"       : m["changed"],
            "columnNumber"  : m["columnNumber"],
            "created"       : m["created"],
            "deleted"       : m["deleted"],
            "fileName"      : m["fileName"],
            "fullName"      : m["fullName"],
            "id"            : m["id"],
            "lineNumber"    : m["lineNumber"],
            "problem"       : m["problem"],
            "problemType"   : m["problemType"],
            "success"       : m["success"]
        })
    return return_messages

def parse_run_test_result(res):
    return_result = {}
    return_run_tests = {}
    code_coverage = []
    code_coverage_return = []
    code_coverage_warnings = []
    failures = []
    successes = []
    if 'codeCoverage' in res['runTestResult'] and type(res['runTestResult']['codeCoverage']) is not list:
        code_coverage = [res['runTestResult']['codeCoverage']]
    else:
        code_coverage = res['runTestResult']['codeCoverage']
    if 'codeCoverageWarnings' in res['runTestResult'] and type(res['runTestResult']['codeCoverageWarnings']) is not list:
        code_coverage_warnings = [res['runTestResult']['codeCoverageWarnings']]
    else:
        code_coverage_warnings = res['runTestResult']['codeCoverageWarnings']
    if 'failures' in res['runTestResult'] and type(res['runTestResult']['failures']) is not list:
        failures = [res['runTestResult']['failures']]
    else:
        failures = res['runTestResult']['failures']
    if 'successes' in res['runTestResult'] and type(res['runTestResult']['successes']) is not list:
        successes = [res['runTestResult']['successes']]
    else:
        successes = res['runTestResult']['successes']
    
    for c in code_coverage:
        code_coverage_return.append({
            "changed"       : m["changed"],
            "columnNumber"  : m["columnNumber"],
            "created"       : m["created"],
            "deleted"       : m["deleted"],
            "fileName"      : m["fileName"],
            "fullName"      : m["fullName"],
            "id"            : m["id"],
            "lineNumber"    : m["lineNumber"],
            "problem"       : m["problem"],
            "problemType"   : m["problemType"],
            "success"       : m["success"]
        })
    return_result['codeCoverage'] = code_coverage_return
    return return_result

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)

def list_grouper(n, iterable):
    args = [iter(iterable)] * n
    return ([e for e in t if e != None] for t in itertools.izip_longest(*args))
     