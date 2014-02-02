import sys
import pprint
import json
sys.path.append('../')
sys.path.append('../../')

from lib.connection import PluginConnection

params = {
	"project_name" 		: "rc2",
	"client" 			: "SUBLIME_TEXT_3",
    "workspace"         : "/Users/josephferraro/Development/st"
}
connection = MavensMatePluginConnection(params)
#test_result = connection.project.run_unit_tests(params)
test_result = connection.project.run_unit_tests_async()

#print resp

print json.dumps(test_result, sort_keys=True,indent=4)
#result = process_unit_test_result(obj)
#config.logger.debug('\n\n\n\n\n')
#config.logger.debug(json.dumps(result, sort_keys=True,indent=4))

#html = util.generate_html_response('unit_test', test_result, params)
#print util.generate_success_response(html, "html")


#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(test_result)