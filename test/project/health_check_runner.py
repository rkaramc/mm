import sys
import pprint

sys.path.append('../')
sys.path.append('../../')

from lib.health_check import HealthCheck
#check = HealthCheck("/Users/josephferraro/Development/Github/mm/test/test_workspace/unit test health check project")
#check = HealthCheck("/Users/josephferraro/Development/st/rc9")
check = HealthCheck("/Users/josephferraro/Development/st/dreamforce")

result = check.run()
pp = pprint.PrettyPrinter(indent=2)
pp.pprint(result)