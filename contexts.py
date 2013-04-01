import life as lfe

import encounters
import graphics
import alife

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
		encounters.create_encounter(life, phrase['from'])
	elif phrase['gist'] == 'surrender':
		_reactions.append({'type': 'say','text': 'Stay still!',
			'communicate': 'stand_still'})
		_reactions.append({'type': 'say','text': 'Drop everything.',
			'communicate': 'comply|drop_everything|stand_still'})
	elif phrase['gist'] == 'share_camp_info':
		lfe.memory(life, 'heard about camp',
			camp=phrase['camp']['id'],
			target=phrase['from']['id'])
		
		alife.camps.discover_camp(life, phrase['camp'])		
		graphics.message('You discovered a camp via %s.' % (' '.join(phrase['from']['name'])), style='important')
	elif phrase['gist'] == 'welcome_to_camp':
		_reactions.append({'type': 'say','text': 'Good to be here!',
			'communicate': 'greeting'})
	else:
		logging.warning('Unhandled player context: %s' % phrase['gist'])

	return _reactions

def create_context(life, action):
	logging.debug('** Created new context **')
	
	if 'gist' in action:
		_reactions = _create_context_from_phrase(life, action)

	return {'action': 'None',
		'text': 'Nothing here!',
		'items': [],
		'reactions': _reactions,
		'from': action['from'],
		'time': 150}
