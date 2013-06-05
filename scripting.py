#Command
#CREATE_ITEM(<item name>, <pos>)

import logging
import re

def parse(owner, text):
	_functions = get_functions(owner, text)
	
	return _functions

def parse_arguments(owner, arguments):
	_returned_arguments = []
	for arg in [arg.strip().rstrip(')') for arg in arguments.split(',')]:
		_returned_arguments.append(parse_argument(owner, arg))
	
	return _returned_arguments

def parse_argument(owner, argument):
	for match in re.findall('(self.[a-zA-Z_]*)', argument):
		_value = match.split('.')[1]
		
		if not _value in owner:
			logging.error('Script error: \'%s\' not found in self.' % _value)
			return None
		
		return owner[_value]
	
	return argument

def get_functions(owner, text):
	_functions = {}

	for function in re.findall('[a-zA-Z_]*\(.*\)', text):
		_name,_args = function.split('(')
		_functions[_name] = parse_arguments(owner, _args)

	return _functions

#if __name__ == "__main__":
#	print parse({'pos': (5,10)},'CANDISMANTLE[CREATE_ITEM(white cloth, self.pos)]')