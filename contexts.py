import life as lfe
import logging

def _create_context_from_phrase(life, phrase):
	_reactions = []
	
	if phrase['gist'] == 'comply':
		_reactions.append({'action': 'say','text': 'I give up!'})
		
		if lfe.get_held_items(life, matches=[{'type': 'gun'}]):
			_reactions.append({'action': 'action','text': '<Shoot %s>' % ' '.join(phrase['from']['name'])})
	
	return _reactions

def create_context(life, action):
	logging.debug('Created new context.')
	
	if 'gist' in action:
		return _create_context_from_phrase(life, action)

	return [{'action': 'None','text': 'Nothing here!'}]
