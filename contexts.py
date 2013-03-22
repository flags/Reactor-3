import life as lfe

import encounters

import logging

def _create_context_from_phrase(life, phrase):
	_reactions = []
	
	if phrase['gist'] == 'comply':
		_reactions.append({'type': 'say','text': 'I give up!',
			'communicate': 'surrender'})
		
		if lfe.get_held_items(life, matches=[{'type': 'gun'}]):
			_reactions.append({'action': 'action',
				'text': '<Shoot %s>' % ' '.join(phrase['from']['name'])})
	elif phrase['gist'] == 'demand_drop_item':
		_reactions.append({'type': 'action','text': 'Drop the item.',
			'action': {'action': 'dropitem','item': phrase['item']},
			'score': 900,
			'delay': lfe.get_item_access_time(life,phrase['item']),
			'communicate': 'compliant'})
	elif phrase['gist'] == 'greeting':
		_reactions.append({'type': 'say','text': 'Hello there!',
			'communicate': 'greeting'})
		_reactions.append({'type': 'say','text': 'You\'re a jerk.',
			'communicate': 'insult'})
	elif phrase['gist'] == 'surrender':
		_reactions.append({'type': 'say','text': 'Stay still!',
			'communicate': 'stand_still'})
		_reactions.append({'type': 'say','text': 'Drop everything.',
			'communicate': 'comply|drop_everything|stand_still'})
	else:
		logging.warning('Unhandled player context: %s' % phrase['gist'])

	return _reactions

def create_context(life, action):
	logging.debug('Created new context.')
	encounters.create_encounter(life, action['from'])
	
	if 'gist' in action:
		return _create_context_from_phrase(life, action)

	return [{'action': 'None','text': 'Nothing here!'}]
