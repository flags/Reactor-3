from globals import SETTINGS, LIFE

import life as lfe

import encounters
import graphics
import dialog
import alife
import logic

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
			'communicate': 'dropped_demanded_item'})
	
	elif phrase['gist'] == 'dialog':
		if not phrase['dialog_id'] in LIFE[SETTINGS['controlling']]['dialogs']:
			life['dialogs'].append(phrase['dialog_id'])
		
		if dialog.get_last_message(phrase['dialog_id'])['text']:
			logic.show_event(dialog.get_last_message(phrase['dialog_id'])['text'], life=phrase['from'])
		
		if lfe.has_dialog(LIFE[SETTINGS['controlling']]):
			dialog.process(LIFE[SETTINGS['controlling']], lfe.has_dialog(LIFE[SETTINGS['controlling']]))
	
	elif phrase['gist'] == 'looks_hostile':
		#encounters.create_encounter(life, phrase['from'])
		#logic.show_event(
		alife.speech.start_dialog(phrase['from'], life['id'], 'encounter')
	#else:
	#	logging.warning('Unhandled player context: %s' % phrase['gist'])

	return _reactions

def create_context(life, action, timeout_callback=None):
	#logging.debug('** Created new context %s **' % action['gist'])
	
	if 'gist' in action:
		_reactions = _create_context_from_phrase(life, action)

	return {'action': 'None',
		'text': 'Nothing here!',
		'items': [],
		'reactions': _reactions,
		'from': action['from'],
		'timeout_callback': timeout_callback,
		'time': 150}
