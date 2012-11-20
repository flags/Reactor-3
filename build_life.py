from globals import *
import os

def read_xml_file(file):
	_file = []
	
	with open(os.path.join(LIFE_DIR,file),'r') as e:
		for line in e.readlines():
			line = line.strip()
			
			if not line:
				continue
			
			_file.append(line)
		
		return _file
	
	raise Exception('Could not read file: ' % os.path.join(LIFE_DIR,file))

def get_value(data,value):
	for entry in data:
		if entry.count(value):
			return entry.partition('>')[2].partition('</')[0]
	
	raise Exception('Cannot find value: %s' % value)

def get_tag_info(data,tag):
	for entry in data:
		if entry.count('<%s>' % tag):
			pass

def get_tag(data,tag):
	_start = -1
	
	for entry in data:
		if _start == -1 and entry.count('<%s' % tag):
			_start = data.index(entry)+1
		
		if _start>-1 and entry.count('</%s>' % tag):
			return get_children_of_tag(data[_start:data.index(entry)])
	
	raise Exception('Could not find tag: %s' % tag)

def get_children_of_tag(taglist):
	_children = []
	
	for tag in taglist:
		if tag.count('/'):
			continue
		
		_children.append(tag.replace('<','').replace('>',''))
	
	return _children

def build(file):
	_data = read_xml_file(file)
	
	life = {}
	
	life['race'] = get_value(_data,'race')
	print get_tag(_data,'hip')
	
	return life

print '*'*10
print 'BUILD LIFE'
print '*'*10
print build('human.xml')