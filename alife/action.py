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
	if 'life' in  action['kwargs']:
		life = LIFE[action['kwargs']['life']]
	
	if 'add_to' in action['kwargs']:
		_add_to = action['kwargs']['add_to']
	else:
		_add_to = []
	
	if 'retrieve' in action['kwargs']:
		_list = retrieve(action['kwargs']['retrieve'], life=life)
	
	if 'filter_by' in action['kwargs']:
		for entry in action['kwargs']['filter_by']:
			if entry in action['kwargs']['add_to']:
				_add_to.remove(entry)
	
	if 'matching' in action['args']:
		_match_mask = action['kwargs']['matching']
	else:
		_match_mask = {'id': '*'}
	
	if 'question' in action['kwargs']:
		lfe.create_question(life,
	        action['kwargs']['question'],
	        _match_mask,
	        action['kwargs']['callback'],
	        action['kwargs']['answer'])
		
		print 'ASKING QUESTION' * 50
	
	if 'find_alife' in action['args']:
		return life['know'].keys()
	
	if 'track_alife' in action['args']:
		print action['kwargs'], _list
		if not _list:
			return False
		
		if movement._find_alife(life, target=_list[0]):
			if not _list[0] in _add_to:
				_add_to.append(_list[0])
		
		print 'WERE TRACKING' * 50
		lfe.focus_on(life)
		
		return True

def execute(action):
	#try:
	return _execute(action)
	#except KeyError:
	#	return MISSING_KEY_IN_ACTION
	