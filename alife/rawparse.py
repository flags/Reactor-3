import stats
import re

FUNCTION_MAP = {'is_family': stats.is_family}

def create_rawlangscript():
	return {'section': '', 'sections': {}}

def create_section(script, section):
	script['sections'][section] = {}
	print 'Section: %s' % section

def set_active_section(script, section):
	script['section'] = section
	print 'Active: %s' % section

def create_action(script, identifier, arguments):
	_args = []
	
	for argument in arguments:
		if argument.count('['):
			bracket_data = [entry.strip('[').strip(']') for entry in re.findall('\[[\w]*\]', argument)]
			_args.extend(bracket_data)
		else:
			_args.append(argument)
		
	return {'id': identifier, 'arguments': _args}

def add_action(script, action):
	script['sections'][script['section']][action['id']] = action['arguments']

def parse(script, line, filename='', linenumber=0):
	if not line.count('[') == line.count(']'):
		raise Exception('Brace mismatch (%s, line %s): %s' % (filename, linenumber, line))
	
	bracket_data = [entry.strip('[').strip(']') for entry in re.findall('\[[\w]*\]', line)]
	curly_brace_data = [entry.strip('[').strip(']') for entry in re.findall('\[[\w]*\]', line)]
	
	if line.startswith('['):
		create_section(script, bracket_data[0])
		set_active_section(script, bracket_data[0])
	
	elif script['section'] and line.count(':'):
		_split = line.split(':')
		identifier = _split[0]
		arguments = _split[1].split(',')
		add_action(script, create_action(script, identifier, arguments))

def read(filename):
	_script = create_rawlangscript()
	with open(filename, 'r') as e:
		_i = 1
		for line in e.readlines():
			if line.startswith('#'):
				continue
			
			parse(_script, line.strip().lower(), filename=filename, linenumber=_i)
			_i += 1
	
	return _script

def raw_has_section(life, section):
	if section in life['raw']['sections']:
		return True
	
	return False

def translate(function):
	return FUNCTION_MAP[function]