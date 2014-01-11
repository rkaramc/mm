import sys
import pprint
import json
sys.path.append('../')

sys.path.append('../../')
from lib.mm_connection import MavensMatePluginConnection
import lib.mm_util as mm_util
import lib.xmltodict as xmltodict

params = {
	"project_name" 	: "myproject",
	"client" 	: "SUBLIME_TEXT_3"
}
connection = MavensMatePluginConnection(params)
resp = connection.project.index_metadata()
#describe_result = connection.project.sfdc_client.describeMetadata(retXml=True)
#d = xmltodict.parse(describe_result,postprocessor=mm_util.xmltodict_postprocessor)
#result = d["soapenv:Envelope"]["soapenv:Body"]["describeMetadataResponse"]["result"]
#print json.dumps(result, indent=4)
print resp
