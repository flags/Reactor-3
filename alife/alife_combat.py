from globals import *

import combat
import speech
import brain

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
	
	_targets = []
	_neutral_targets = []
	_all_targets = targets_seen
	_all_targets.extend(targets_not_seen)
	
	for _target in _all_targets[:]:
		if 'surrendered' in _target['who']['flags'] and not brain.get_alife_flag(life, _target['who']['life'], 'not_handling_surrender'):
			_neutral_targets.append(_target)
			_all_targets.remove(_target)
			continue
		
		_targets.append(_target)
	
	brain.store_in_memory(life, 'combat_targets', _all_targets)
	brain.store_in_memory(life, 'neutral_combat_targets', _neutral_targets)
	
	if not brain.retrieve_from_memory(life, 'combat_target'):
		return False
		
	if (not len(targets_seen) and not len(targets_not_seen)) or not combat.weapon_equipped_and_ready(life):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	if combat.has_weapon(life) and _all_targets:
		if not combat.weapon_equipped_and_ready(life):
			if not 'equipping' in life:
				if combat._equip_weapon(life):
					life['equipping'] = True
			
			if _all_targets:
				combat.combat(life, _all_targets[0]['who'], life['map'])
	elif _neutral_targets:
		for _ntarget in [_target['who']['life'] for _target in _neutral_targets]:
			_has_weapon = combat.get_equipped_weapons(_ntarget)
			
			if _has_weapon:
				if not speech.has_sent(life, _ntarget, 'demand_drop_item'):
					combat.disarm(life, _ntarget, _has_weapon[0])
			else:
				continue
