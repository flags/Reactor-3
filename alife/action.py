from globals import MISSING_KEY_IN_ACTION

import life as lfe

import logging

def make(*args, **kwargs):
	logging.debug('Created action:', args, kwargs)
	
	return {'args': args, 'kwargs': kwargs}
	
def _execute(action):
	print 'OKAY' * 10
	
	if 'talk' in action['args']:
		if 'match' in action['kwargs']:
			_match_mask = action['kwargs']['match']
		else:
			_match_mask = {'id': '*'}
			
		if 'question' in action['kwargs']:
			#lfe.create_question(life,
			#		'where_is_target',
			#		{'target': _info['founder']},
			#		lfe.get_memory,
			#		{'text': 'location_of_target', 'target': _info['founder'], 'location': '*'})
			lfe.create_question(life,
				action['kwargs']['question'],
				_match_mask,
				action['kwargs']['callback'],
			    action['kwargs']['answer'])

def execute(action):
	try:
		return _execute(action)
	except KeyError:
		return MISSING_KEY_IN_ACTION
	