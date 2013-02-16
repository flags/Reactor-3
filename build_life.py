from globals import *
import json
import sys
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

def save_json_file(file,data):
	with open(os.path.join(LIFE_DIR,file),'w') as e:
		e.write(json.dumps(data,indent=2))

def get_value(data,value):
	for entry in data:
		if entry.count(value):
			return entry.partition('>')[2].partition('</')[0]

	raise Exception('Cannot find value: %s' % value)

def get_tag(data,tag):
	_start = -1
	
	for entry in data:
		if _start == -1 and entry.count('<%s' % tag):
			_start = data.index(entry)+1
		
		if _start>-1 and entry.count('</%s>' % tag):
			return get_children_of_tag(data[_start:data.index(entry)])
	
	raise Exception('Could not find tag: %s' % tag)

def connect_limb(name,limb,to,start):
	for limb2 in start:		
		if to == limb2:
			start[limb2]['attached'][name] = limb
			return True
		
		connect_limb(name,limb,to,start[limb2]['attached'])

def get_children_of_tag(taglist):
	_limbs = {}
	_name = ''
	_flags = ''
	_parent = ''
	_damage_mod = 0
	
	for tag in taglist:		
		_key = tag.partition('<')[2].partition('>')[0]
		
		if _key.count('/'):
			if not _parent:
				_limbs[_name] = {'flags': _flags}
			else:
				_limb = {'flags': _flags}
				_limb['parent'] = _parent
				_limb['damage_mod'] = _damage_mod
				_limbs[_name] = _limb
				
				#if _parent in _limbs:
				#	_limbs[_parent]['attached'][_name] = _limb
				#else:
				#	connect_limb(_name,_limb,_parent,_limbs)
			
			_name = ''
			_flags = ''
			_parent = ''
			continue
		
		_value = tag.partition('>')[2].rpartition('</')[0]
		
		if not _value:
			_name = _key
		else:
			if _key == 'flags':
				_flags = _value
			
			if _key == 'parent':
				_parent = _value
			
			if _key == 'damage_mod':
				_damage_mod = _value
	
	return _limbs

def build(file):
	print 'Reading file \'%s\'...' % file
	
	try:
		_data = read_xml_file(file)
	except Exception, e:
		print 'Failed to read file:',e
		return False
	
	life = {}	
	life['race'] = get_value(_data,'race')
	life['flags'] = get_value(_data,'flags')
	life['icon'] = get_value(_data,'icon')

	print 'Creating new life: %s' % life['race']
	print 'Parsing and connecting limbs...',
	
	life['body'] = get_tag(_data,'body')
	
	print 'Done!'
	print 'Offloading to disk...',
	save_json_file('%s.json' % life['race'],life)
	print 'Done!'
	
	return True

print '*'*10
print 'Build Life'
print '*'*10

if len(sys.argv) == 1:
	print 'Usage: python build_life.py <files>'
else:
	for life in sys.argv[1:]:
		build(life)
