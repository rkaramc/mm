import sys
import pprint
import json

sys.path.append('../')

import lib.crawlJson as crawlJson
import lib.mm_util as util
from lib.mm_connection import MavensMatePluginConnection

params = {
	"project_name" 		: "bloat",
	"client" 			: "SUBLIME_TEXT_3",
	"classes" 			: ["compile_and_test_one_off"],
	"api" 				: "m",
	"debug_categories" 	: [{'category': 'Apex_code', 'level': 'DEBUG'}]
}
connection = MavensMatePluginConnection(params)
test_result = connection.project.run_unit_tests(params)
#print resp

print json.dumps(test_result, sort_keys=True,indent=4)
#result = process_unit_test_result(obj)
#config.logger.debug('\n\n\n\n\n')
#config.logger.debug(json.dumps(result, sort_keys=True,indent=4))

#html = util.generate_html_response('unit_test', test_result, params)
#print util.generate_success_response(html, "html")


#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(test_result)