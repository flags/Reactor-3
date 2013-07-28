import judgement
import survival
import numbers
import combat
import stats
import logic

import re

def always(life):
	return True

def never(life):
	return False

CURLY_BRACE_MATCH = '{[\w+-\.,]*}'
FUNCTION_MAP = {'is_family': stats.is_family,
	'is_same_species': stats.is_same_species,
	'is_compatible_with': stats.is_compatible_with,
	'can_bite': stats.can_bite,
	'can_scratch': stats.can_scratch,
	'weapon_equipped_and_ready': combat.weapon_equipped_and_ready,
	'prepare_for_ranged': combat.prepare_for_ranged,
	'explore_unknown_chunks': survival.explore_unknown_chunks,
	'is_nervous': stats.is_nervous,
	'is_aggravated': stats.is_aggravated,
	'is_safe': judgement.is_safe,
	'is_healthy': None,
	'closest': None,
	'kill': None,
	'has_attacked_trusted': stats.has_attacked_trusted,
	'distance_to_pos': stats.distance_from_pos_to_pos,
	'is_idle': lambda life: life['state'] == 'idle',
	'is_child': stats.is_child,
	'is_parent': stats.is_parent,
	'is_night': logic.is_night,
	'always': always,
	'never': never}

def create_rawlangscript():
	return {'section': '', 'sections': {}}

def create_section(script, section):
	script['sections'][section] = {}

def set_active_section(script, section):
	script['section'] = section

def create_action(script, identifier, arguments):
	_args = []
	
	for argument in arguments:
		if argument.count('['):
			bracket_data = [entry.strip('[').strip(']') for entry in re.findall('\[[\w]*\]', argument)]
			curly_BRACE_data = [entry.strip('{').strip('}') for entry in re.findall(CURLY_BRACE_MATCH, argument)]
			_args.append({'function': argument.split('[')[0]})
		else:
			curly_BRACE_data = re.findall(CURLY_BRACE_MATCH, argument)
			
			if curly_BRACE_data:
				argument = [argument.replace(entry, '') for entry in curly_BRACE_data][0]
				curly_BRACE_data = [data.strip('{').strip('}') for data in curly_BRACE_data][0].split(',')
				_arguments = curly_BRACE_data
				_values = []
				
				for value in _arguments:
					_arg = {}
					
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
			
			#print argument, curly_BRACE_data
			
			_true = True
			_string = ''
			_self_call = False
			_no_args = False
			if argument.startswith('\"'):
				argument = argument.replace('\"', '')
				_string = argument
			elif argument.startswith('%'):
				argument = argument[1:]
				_no_args = True
			elif argument.startswith('!'):
				argument = argument[1:]
				_true = False
			elif argument.startswith('@'):
				argument = argument[1:]
				_self_call = True
			elif argument.startswith('*'):
				argument = argument[1:]
				_true = '*'
			
			if _string:
				_args.append({'string': _string})
			else:
				_args.append({'function': translate(argument),
					'values': _values,
					'true': _true,
					'string': None,
					'self_call': _self_call,
					'no_args': _no_args})
		
	return {'id': identifier, 'arguments': _args}

def add_action(script, action):
	script['sections'][script['section']][action['id']] = action['arguments']

def parse(script, line, filename='', linenumber=0):
	if not line.count('[') == line.count(']'):
		raise Exception('BRACE mismatch (%s, line %s): %s' % (filename, linenumber, line))
	
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
	if not function in FUNCTION_MAP:
		raise Exception('\'%s\' is not a valid raw script function.' % function)
	
	return FUNCTION_MAP[function]
