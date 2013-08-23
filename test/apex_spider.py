import urllib2
from BeautifulSoup import BeautifulSoup

types = [
	'blob', 'string', 'set', 'list', 'date', 'datetime', 'boolean', 'double', 'id', 'integer', 'long', 'time', 'map', 'enum'
]

types = [
	'datetime'
]

for t in types:
	print 'processing --> ', t
	d = {
		"instance_methods" : [

		],
		"static_methods" : [

		]
	}

	soup = BeautifulSoup(urllib2.urlopen('http://www.salesforce.com/us/developer/docs/apexcode/Content/apex_methods_system_'+t+'.htm').read())

	tables = soup('table', {'class' : 'featureTable'})

	#static
	for row in tables[0].tbody('tr'):
	  print "--row--"
	  tds = row('td')
	  method_name = tds[0].find('samp').string
	  
	  try:
	  	contents = tds[1].contents
	  	arguments = ''
	  	print len(contents)
	  	if len(contents) == 2:
	  		arguments = contents[0].strip()+"_"+contents[1].string
	  	elif len(contents) > 2:
	  		args=[]
			args.append(contents[0].strip()+"_"+contents[1].string.lower())
		  	for i, c in enumerate(contents):
		  		if i > 1:
		  			print 'c: ', c.contents
		  			inner_contents = c.contents
		  			args.append(inner_contents[0].strip()+"_"+inner_contents[1].string.lower()) 

		  	arguments = ', '.join(args)
	  	print 'args: ', arguments
	  	#arguments += "_"+tds[1].find('var').string
	  except Exception, e:
	  	print e
	  	arguments = ''

	  return_type = tds[2].string
	  try:
	  	description = tds[3].string
	  except:
	  	description = 'None'
	  
	  # print method_name
	  # print arguments
	  # print return_type
	  # print description

	  d["instance_methods"].append(
	  	"{0}({1})".format(method_name, arguments)
	  )

	# if len(tables) > 1:
	# 	#instance
	# 	for row in tables[1].tbody('tr'):
	# 	  print "--row--"
	# 	  tds = row('td')
	# 	  method_name = tds[0].find('samp').string
		  
	# 	  try:
	# 	  	arguments = tds[1].find('var').string
	# 	  except:
	# 	  	arguments = ''
		  
	# 	  return_type = tds[2].string
		  
	# 	  try:
	# 	  	description = tds[3].string
	# 	  except:
	# 	  	description = 'None'

	# 	  print method_name
	# 	  print arguments
	# 	  print return_type
	# 	  print description

	print d