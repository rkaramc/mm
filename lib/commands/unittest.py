import os
import shutil
import requests
import time
import datetime
import json
import lib.xmltodict as xmltodict
import lib.config as config
import lib.util as util
from lib.exceptions import *
from lib.basecommand import Command
from debug import NewQuickTraceFlagCommand

debug = config.logger.debug

class RunAllTestsAsyncCommand(Command):
    aliases=["run_all_tests"]
    def execute(self):
        return config.sfdc_client.run_async_apex_tests(None, False, True)

class RunUnitTestsAsyncCommand(Command):
    aliases=["unit_test","test"]
    """
        Runs Apex tests via the sfdc async testing api
        (REPLACEMENT API FOR TEST RUNNER, because it updates coverage stats)
    """
    def execute(self):
        if int(float(util.SFDC_API_VERSION)) <= 28 or config.connection.get_plugin_client_setting("mm_use_legacy_test_ui", False):
            #raise MMException("This command requires mm_api_version to be set to 29.0 or higher.")
            return RunUnitTestsCommand(params=self.params,args=self.args).execute()

        project = config.project
        sfdc_client = config.sfdc_client

        generate_logs = self.params.get("generate_logs", False)
        if generate_logs:
            NewQuickTraceFlagCommand(params={"running_user_only":True}).execute()

        test_classes = self.params.get("classes", None)
        debug('running tests for')
        debug(test_classes)
        if test_classes == None or test_classes == []: #need to run all tests in project
            classes = []
            triggers = []
            test_classes = []
            for dirname, dirnames, filenames in os.walk(os.path.join(project.location,"src","classes")):
                for filename in filenames:
                    if "test" in filename.lower() and "-meta.xml" not in filename:
                        test_classes.append(util.get_file_name_no_extension(filename))
                    elif "-meta.xml" not in filename:
                        classes.append(util.get_file_name_no_extension(filename))
            for dirname, dirnames, filenames in os.walk(os.path.join(project.location,"src","triggers")):
                for filename in filenames:
                    if "-meta.xml" not in filename:
                        triggers.append(util.get_file_name_no_extension(filename))
        else: #user has specified certain tests to run
            classes = []
            triggers = []
            for dirname, dirnames, filenames in os.walk(os.path.join(project.location,"src","classes")):
                for filename in filenames:
                    if "test" not in filename.lower() and "-meta.xml" not in filename:
                        classes.append(util.get_file_name_no_extension(filename))
            for dirname, dirnames, filenames in os.walk(os.path.join(project.location,"src","triggers")):
                for filename in filenames:
                    if "-meta.xml" not in filename:
                        triggers.append(util.get_file_name_no_extension(filename))
        
        params = { "files" : test_classes }
        test_results = sfdc_client.run_async_apex_tests(params, False)
        
        params = { "classes" : classes, "triggers" : triggers, "test_classes" : test_classes }
        coverage_report = sfdc_client.get_apex_test_coverage(params, transform_ids=True)
        debug(">>>>>>>>>>")
        debug(coverage_report)
        result = {
            "test_results"  : test_results,
            "coverage"      : coverage_report
        }

        if self.args.respond_with_html:
            html = util.generate_html_response(self.args.operation, result, self.params)
            return util.generate_success_response(html, "html")
        else:
            return result

class RunUnitTestsCommand(Command):    
    name="test_legacy"
    """
        executes 1 or more unit tests using the metadata api endpoint
        (LEGACY TEST RUNNER ENDPOINT, does NOT update coverage in the org)
    """
    def execute(self):
        sfdc_client = config.sfdc_client
 
        empty_package_xml = util.get_empty_package_xml_contents()
        tmp, tmp_unpackaged = util.put_tmp_directory_on_disk(True)
        util.put_empty_package_xml_in_directory(tmp_unpackaged, empty_package_xml)
        zip_file = util.zip_directory(tmp, tmp)
        deploy_params = {
            "zip_file"          : zip_file,
            "rollback_on_error" : True,
            "ret_xml"           : True,
            "classes"           : self.params.get('classes', []),
            "debug_categories"  : self.params.get('debug_categories', [])
        }
        deploy_result = sfdc_client.deploy(deploy_params,is_test=True)
        #debug(deploy_result)
        d = xmltodict.parse(deploy_result,postprocessor=util.xmltodict_postprocessor)
        if int(float(util.SFDC_API_VERSION)) >= 29:
            result = d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']['details']['runTestResult']
        else:
            result = d["soapenv:Envelope"]["soapenv:Body"]['checkDeployStatusResponse']['result']['runTestResult']

        try:
            result['log'] = d["soapenv:Envelope"]["soapenv:Header"]["DebuggingInfo"]["debugLog"]
        except:
            result['log'] = 'Log not available.'

        shutil.rmtree(tmp)

        if self.args.respond_with_html:
            html = util.generate_html_response(self.args.operation, result, self.params)
            return util.generate_success_response(html, "html")
        else:
            return result

class RunAsyncApexTestsCommand(Command):
    name="test_async"
    """
        Pass in Apex tests classes to run (currently not used within a UI) (could be replaced)
        run_async_apex_tests
    """
    def execute(self):
        return config.sfdc_client.run_async_apex_tests(self.params, False)

class CodeCoverageReportCommand(Command):
    aliases=["coverage_report"]
    """
        Retrieves a test coverage report for each Apex Class & Apex Trigger in a project
    """
    def execute(self):
        project = config.project
        classes = []
        triggers = []
        if os.path.isdir(os.path.join(project.location,"src","classes")):
            for dirname, dirnames, filenames in os.walk(os.path.join(project.location,"src","classes")):
                for filename in filenames:
                    if "test" not in filename.lower() and "-meta.xml" not in filename:
                        classes.append(util.get_file_name_no_extension(filename))
        if os.path.isdir(os.path.join(project.location,"src","triggers")):
            for dirname, dirnames, filenames in os.walk(os.path.join(project.location,"src","triggers")):
                for filename in filenames:
                    if "-meta.xml" not in filename:
                        triggers.append(util.get_file_name_no_extension(filename))

        params = {
            "classes"   : classes,
            "triggers"  : triggers
        }
        return config.sfdc_client.get_apex_test_coverage(params, True)

class GetApexTestCoverageCommand(Command):
    aliases=["get_coverage"]
    """
        Pass in a list of classes and/or triggers and receive a coverage report
    """
    def execute(self):
        return config.sfdc_client.get_apex_test_coverage(self.params, transform_ids=True)

class GetOrgWideTestCoverageCommand(Command):
    """
        Gets percent coverage on all Apex in the org
    """
    def execute(self):
        return config.sfdc_client.get_org_wide_test_coverage()



