from globals import *

import life as lfe

import judgement
import brain

import logging

STATE = 'in group'

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		if judgement.is_target_dangerous(life, entry['who']['life']['id']):
			_score += entry['danger']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if life['state'] in ['combat', 'working']:
		return False
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
		return False
	
	_top_invite = {'fondness': 0, 'leader': None}
	for memory in lfe.get_memory(life, matches={'text': 'was invited to group'}):
		_known = brain.knows_alife_by_id(life, memory['target'])
		
		if not _known or (_known and _known['fondness']<1):
			continue
		
		if not _top_invite['leader'] or _known['fondness']>_top_invite['fondness']:
			_top_invite['fondness'] = _known['fondness']
			_top_invite['leader'] = _known['life']
	
	brain.store_in_memory(life, 'following', _top_invite['leader'])
	
	if not _top_invite['leader']:
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_following = brain.retrieve_from_memory(life, 'following')
	
	lfe.add_action(life,{'action': 'move',
		'to': [_following['pos'][0], _following['pos'][1]]},
		200)
