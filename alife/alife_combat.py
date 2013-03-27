from globals import *

import combat

import logging

STATE = 'combat'
ENTRY_SCORE = -1

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if not calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) <= ENTRY_SCORE:
		return False
	
	if not len(targets_seen) and not len(targets_not_seen):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#TODO: Ugly hack. We're already doing this in alife_hidden.py
	if combat.has_weapon(life):
		if not combat._weapon_equipped_and_ready(life):
			if not 'equipping' in life:
				if combat._equip_weapon(life):
					life['equipping'] = True
		else:
			_targets = targets_seen
			_targets.extend(targets_not_seen)
			combat.combat(life, _targets[0]['who'], life['map'])
