from globals import *

import life as lfe

import judgement
import numbers
import combat
import speech
import camps
import brain
import jobs

import logging

STATE = 'combat'
ENTRY_SCORE = -1

def setup(life):
	brain.store_in_memory(life, 'targets', judgement.get_targets(life))	

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	_all_targets = []
	_combat_targets = judgement.get_targets(life)
	
	if not _combat_targets:
		return False
	
	if not brain.retrieve_from_memory(life, 'combat_targets'):
		return False
	
	if not combat.weapon_equipped_and_ready(life):
		print life['name'],'Not ready to engage'
		return False
	
	return RETURN_VALUE

#TODO: Use judgement.get_nearest_threat()
def get_closest_target(life, targets):
	_closest = {'dist': -1, 'life': None}
	
	for target in targets:
		_know = brain.knows_alife_by_id(life, target)
		_dist = numbers.distance(life['pos'], _know['last_seen_at'])
		
		if _dist<_closest['dist'] or not _closest['life']:
			_closest['life'] = target
			_closest['dist'] = _dist
	
	return _closest['life']

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_all_targets = brain.retrieve_from_memory(life, 'combat_targets')
	
	if combat.has_weapon(life) and _all_targets:
		if not combat.weapon_equipped_and_ready(life):
			if not 'equipping' in life:
				if combat._equip_weapon(life):
					life['equipping'] = True
			
		if _all_targets:
			_closest_target = get_closest_target(life, _all_targets)
			combat.combat(life, _closest_target)