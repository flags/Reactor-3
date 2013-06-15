#Command
# CREATE_ITEM(<item name>, <pos>)
# DELETE()

from globals import *

import items
import life

import logging
import re

def parse_console(text):
	return text.replace('pc', 'SETTINGS[\'controlling\']')

def execute(script, **kvargs):
	for function in script:
		_args = parse_arguments(script[function], **kvargs)
		
		if function == 'CREATE_AND_OWN_ITEM':
			_i = items.create_item(_args[0], position=_args[1])
			life.add_item_to_inventory(kvargs['owner'], _i)
		elif function == 'DELETE':
			_i = life.remove_item_from_inventory(kvargs['owner'], kvargs['item'])
			items.delete_item(_i)
		elif function == 'LIGHT_FOLLOW':
			LIGHTS.append({'pos': kvargs['owner']['pos'],
			               'follow_item': kvargs['item_uid'],
			               'color': (255, 0, 255), 'brightness': 2,
			               'shake': 0.4})
		else:
			logging.error('Script: \'%s\' is not a valid function.' % function)

def initiate(owner, text):
	_functions = get_functions(owner, text)
	
	return _functions

def parse_arguments(arguments, **kvargs):
	_returned_arguments = []
	for arg in [arg.strip().rstrip(')') for arg in arguments.split(',')]:
		_returned_arguments.append(parse_argument(kvargs['owner'], arg))
	
	return _returned_arguments

def parse_argument(owner, argument):
	for match in re.findall('(self.[a-zA-Z_]*)', argument):
		_value = match.split('.')[1]
		
		if not _value in owner:
			logging.error('Script syntax: \'%s\' not found in self.' % _value)
			return None
		
		return owner[_value]
	
	return argument

def get_functions(owner, text):
	_functions = {}

	for func in text.split(':'):
		print text
		for function in re.findall('[a-zA-Z_]*\(.*\)', func):
			_name,_args = function.split('(')
			_functions[_name] = _args#parse_arguments(owner, _args)

	return _functions

if __name__ == "__main__":
	print initiate({'pos': (5,10)},'CANDISMANTLE[CREATE_ITEM(white cloth, self.pos)]')