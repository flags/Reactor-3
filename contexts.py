import life as lfe
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
		print phrase.keys()
		_reactions.append({'type': 'action','text': 'Drop the item.',
			'action': {'action': 'dropitem','item': phrase['item']},
			'score': 900,
			'delay': lfe.get_item_access_time(life,phrase['item']),
			'communicate': 'compliant'})
	else:
		logging.warning('Unhandled player context: %s' % phrase['gist'])

	return _reactions

def create_context(life, action):
	logging.debug('Created new context.')
	
	if 'gist' in action:
		return _create_context_from_phrase(life, action)

	return [{'action': 'None','text': 'Nothing here!'}]
