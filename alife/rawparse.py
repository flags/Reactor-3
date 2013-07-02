import stats
import re

CURLY_BRACE_MATCH = '{[\w+-\.,]*}'
FUNCTION_MAP = {'is_family': stats.is_family,
	'is_same_race': stats.is_same_race,
	'can_bite': None,
	'is_healthy': None,
	'closest': None,
	'kill': None}

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
			curly_brace_data = [entry.strip('{').strip('}') for entry in re.findall(CURLY_BRACE_MATCH, argument)]
			_args.append({'function': argument.split('[')[0]})
		else:
			curly_brace_data = re.findall(CURLY_BRACE_MATCH, argument)
			
			if curly_brace_data:
				argument = [argument.replace(entry, '') for entry in curly_brace_data][0]
				curly_brace_data = [data.strip('{').strip('}') for data in curly_brace_data][0].split(',')
				_arguments = curly_brace_data
				_values = []
				
				for value in _arguments:
					_arg = {}
					
					print identifier, _arguments
					if value.count('.'):
						_arg['target'] = value.partition('.')[0]
						_arg['flag'] = value.partition('.')[2].partition('+')[0].partition('-')[0]
						
						if value.count('+'):
							_arg['value'] = int(value.partition('+')[2])
						elif value.count('-'):
							_arg['value'] = -int(value.partition('-')[2])
					
					_values.append(_arg)
				
			else:
				argument = argument.split('{')[0]
				_values = []
			
			#print argument, curly_brace_data
			
			_true = True
			if argument.startswith('!'):
				argument = argument[1:]
				_true = False
			
			_args.append({'function': translate(argument), 'values': _values, 'true': _true})
		
	return {'id': identifier, 'arguments': _args}

def add_action(script, action):
	script['sections'][script['section']][action['id']] = action['arguments']

def parse(script, line, filename='', linenumber=0):
	if not line.count('[') == line.count(']'):
		raise Exception('Brace mismatch (%s, line %s): %s' % (filename, linenumber, line))
	
	bracket_data = [entry.strip('[').strip(']') for entry in re.findall('\[[\w]*\]', line)]
	
	if line.startswith('['):
		create_section(script, bracket_data[0])
		set_active_section(script, bracket_data[0])
	
	elif script['section'] and line.count(':'):
		_split = line.split(':')
		identifier = _split[0]
		
		if _split[1].rpartition('{')[2].rpartition('}')[0].count(','):
			arguments = [_split[1]]
		else:
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