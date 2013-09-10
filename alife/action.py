from globals import LIFE

import life as lfe

import judgement
import movement
import rawparse
import goals

import logging

def retrieve(match, **kwargs):
	if 'goal_id' in match:
		_criteria = goals.get_criteria(kwargs['life'], match['goal_id'], match['criteria_id'])
		return _criteria['result']
	
	if 'list' in match:
		return match['list']
	
	print 'Match returned nothing!'*25
	#if 'criteria_id' in kwargs:
	#	_criteria = goals.get_criteria(life, )

def make(*args, **kwargs):
	logging.debug('Created action: %s', kwargs)
	
	return {'_action': True, 'args': args, 'kwargs': kwargs}

def make_small_script(*args, **kwargs):
	_struct = {'args': [], 'kwargs': {}}
	
	#if 'return' in args:
	#	_struct['args'].append('return')
	
	#if 'return' in args and 'life_id' in args:
	#	return LIFE[kwargs['life_id']]
	
	if 'kwargs' in kwargs:
		_struct['kwargs'].update(kwargs['kwargs'])
	
	if 'function' in kwargs:
		_struct['function'] = kwargs['function']
	#	kwargs['function'](**_struct['arguments'])
	
	return _struct

def execute_small_script(life, action):
	if 'function' in action:
		_args = {}
		for key in action['kwargs']:
			if isinstance(action['kwargs'][key], dict) and 'args' in action['kwargs'][key] and 'return' in action['kwargs'][key]['args']:
				_args[key] = execute_small_script(action['kwargs'][key])
			else:
				_args[key] = action['kwargs'][key]
		
		return rawparse.translate(action['function'])(life, **action['kwargs'])

def _execute(action):
	_struct = {}
	
	if 'life' in  action['kwargs']:
		_struct['life'] = LIFE[action['kwargs']['life']]
	
	if 'add_to' in action['kwargs']:
		_struct['add_to'] = action['kwargs']['add_to']
	else:
		_struct['add_to'] = []
	
	if 'retrieve' in action['kwargs']:
		_struct['list'] = retrieve(action['kwargs']['retrieve'], life=_struct['life'])
	
	if 'store_retrieve_as' in action['kwargs']:
		_struct['store_retrieve_as'] = action['kwargs']['store_retrieve_as']
	
	if 'filter_by' in action['kwargs']:
		for entry in action['kwargs']['filter_by']:
			if entry in _struct['list']:
				_struct['list'].remove(entry)
	
	if 'matching' in action['args']:
		_struct['match_mask'] = action['kwargs']['matching']
	else:
		_struct['match_mask'] = {'id': '*'}
	
	if 'question' in action['kwargs']:
		_struct['question'] = action['kwargs']['question']
	
	if 'ask' in action['args']:
		if not _struct['list']:
			return False
		
		lfe.speech.start_dialog_with_question(_struct['life'], _struct['list'][0], _struct['question'])
		
		if 'add_to' in _struct:
			if not _struct['list'][0] in _struct['list']:
				_struct['add_to'].append(_struct['list'][0])
				print 'LOOK OUT!' * 55, _struct['add_to']
		
		return True
	
	if 'return' in action['args']:
		if 'include' in action['kwargs']:
			_struct.update(action['kwargs']['include'])
		
		return _struct
	
	if 'return_key' in action['args']:
		if 'key' in action['kwargs']:
			return _struct[action['kwargs']['key']]
	
	if 'return_key' in action['kwargs']:
		return _struct[action['kwargs']['return_key']]

	if 'return_function' in action['kwargs']:
		return rawparse.FUNCTION_MAP[action['kwargs']['return_function']]
	
	if 'function' in action['kwargs']:
		_arguments = execute(action['kwargs']['arguments'])
		
		if 'filter' in action['args']:
			_ret_list = []
			
			for key in _arguments.keys():
				if not key in action['kwargs']['arguments']['kwargs']:
					if 'include' in action['kwargs']['arguments']['kwargs'] and key in action['kwargs']['arguments']['kwargs']['include']:
						continue
					
					del _arguments[key]
			
			for result in _struct['list']:
				_arguments.update({_struct['store_retrieve_as']: result})
				if not action['kwargs']['function'](**_arguments):
					_ret_list.append(result)
					continue
				
			for entry in _ret_list:
				_struct['list'].remove(entry)
			
			print 'filter function',_struct['list']
			return _struct['list']
	
	if 'get_known_alife' in action['args']:
		return _struct['life']['know'].keys()
	
	if 'track_alife' in action['args']:
		if not _struct['list']:
			return False
		
		if movement._find_alife(_struct['life'], target=_struct['list'][0]):
			if not _struct['list'][0] in _struct['add_to']:
				_struct['add_to'].append(_struct['list'][0])
				print 'FOUND HIM!!!!!!!!!!!' * 50
		
		lfe.focus_on(_struct['life'])
		print _struct['life']['name'],'Tracking',LIFE[_struct['list'][0]]['name']
		print judgement.can_trust(_struct['life'], _struct['list'][0])
		
		return True

def execute(action):
	#try:
	return _execute(action)
	#except KeyError:
	#	return MISSING_KEY_IN_ACTION
	