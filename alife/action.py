from globals import MISSING_KEY_IN_ACTION, LIFE

import life as lfe

import movement
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
	
	return {'args': args, 'kwargs': kwargs}
	
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
			if entry in action['kwargs']['add_to']:
				_struct['add_to'].remove(entry)
	
	if 'matching' in action['args']:
		_struct['match_mask'] = action['kwargs']['matching']
	else:
		_struct['match_mask'] = {'id': '*'}
	
	#if 'question' in action['kwargs']:
	#	lfe.create_question(_struct['life'],
	#        action['kwargs']['question'],
	#        _struct['match_mask'],
	#        action['kwargs']['callback'],
	#        action['kwargs']['answer'])
	#	
	#	print 'ASKING QUESTION' * 50
	
	if 'return' in action['args']:
		if 'include' in action['kwargs']:
			_struct.update(action['kwargs']['include'])
		
		return _struct
	
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
	
	if 'find_alife' in action['args']:
		return _struct['life']['know'].keys()
	
	if 'track_alife' in action['args']:
		#print action['kwargs'], _struct['list']
		if not _struct['list']:
			return False
		
		if movement._find_alife(_struct['life'], target=_struct['list'][0]):
			if not _struct['list'][0] in _struct['add_to']:
				_struct['add_to'].append(_struct['list'][0])
		
		print 'Tracking'
		lfe.focus_on(_struct['life'])
		
		return True

def execute(action):
	#try:
	return _execute(action)
	#except KeyError:
	#	return MISSING_KEY_IN_ACTION
	