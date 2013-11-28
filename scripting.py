#Command
# CREATE_ITEM(<item name>, <pos>)
# DELETE()

from globals import *

import graphics as gfx

import effects
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
			items.delete_item(ITEMS[kvargs['item_uid']])
		elif function == 'LIGHT_FOLLOW':
			_item = ITEMS[kvargs['item_uid']]
			
			effects.create_light(items.get_pos(kvargs['item_uid']),
			                     (255, 255, 255),
			                     _item['brightness'],
			                     _item['light_shake'],
			                     follow_item=kvargs['item_uid'])
		elif function == 'LIGHT_FOLLOW_REMOVE':
			_item = ITEMS[kvargs['item_uid']]
			
			effects.delete_light_at(items.get_pos(kvargs['item_uid']))
		elif function == 'TOGGLE_BLOCK':
			_item = ITEMS[kvargs['item_uid']]
			
			if _item['blocking']:
				_item['blocking'] = False
			else:
				_item['blocking'] = True
		else:
			logging.error('Script: \'%s\' is not a valid function.' % function)

def initiate(owner, text):
	_functions = get_functions(owner, text)
	
	return _functions

def parse_arguments(arguments, **kvargs):
	_returned_arguments = []
	for arg in [arg.strip().rstrip(')') for arg in arguments.split(',')]:
		_returned_arguments.append(parse_argument(ITEMS[kvargs['item_uid']], arg))
	
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
		for function in re.findall('[a-zA-Z_]*\(.*\)', func):
			_name,_args = function.split('(')
			_functions[_name] = _args#parse_arguments(owner, _args)

	return _functions
