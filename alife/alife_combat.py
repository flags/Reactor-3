from globals import *

import life as lfe

import numbers
import combat
import speech
import camps
import brain
import jobs

import logging

STATE = 'combat'
ENTRY_SCORE = -1

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		if judgement.is_dangerous(life, entry['who']['life']['id']):
			_score += entry['danger']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	#TODO: When are we not safe?
	#if not calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) <= ENTRY_SCORE:
	#	return False
	
	_neutral_targets = []
	_all_targets = []
	
	for target in targets_seen:
		print 'target',target['who'].keys()
		_all_targets.append(target)
	
	for target in targets_not_seen:
		if not target['who']['life']['id'] in [t['who']['life']['id'] for t in _all_targets]:
			_all_targets.append(target)
	
	for _target in _all_targets[:]:
		if lfe.get_memory(life, matches={'target': _target, 'text': 'death'}):
			_all_targets.remove(_target)
			print 'see the dead'
			continue
		
		if jobs.alife_is_factor_of_any_job(_target['who']['life']):
			if life['job']:
				_neutral_targets.append(_target)
			_all_targets.remove(_target)
		
		if brain.get_alife_flag(life, _target['who']['life'], 'not_handling_surrender'):
			_all_targets.remove(_target)
	
	brain.store_in_memory(life, 'combat_targets', _all_targets)
	brain.store_in_memory(life, 'neutral_combat_targets', _neutral_targets)

	#if life['state'] == 'working':
	#	return False
	
	if not brain.retrieve_from_memory(life, 'combat_targets') and not brain.retrieve_from_memory(life, 'neutral_combat_targets'):
		return False
		
	if not combat.weapon_equipped_and_ready(life):
		return False
	
	return RETURN_VALUE

def get_closest_target(life, targets):
	_closest = {'dist': -1, 'life': None}
	for target in targets:
		_dist = numbers.distance(life['pos'], target['who']['life']['pos'])
		
		if _dist<_closest['dist'] or not _closest['life']:
			_closest['life'] = target
			_closest['dist'] = _dist
	
	return _closest['life']

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_all_targets = brain.retrieve_from_memory(life, 'combat_targets')
	_neutral_targets = brain.retrieve_from_memory(life, 'neutral_combat_targets')

	if _all_targets and life['known_camps'] and camps.get_distance_to_nearest_known_camp(life)<30:
		speech.announce(life,
			'camp_raid',
			camp=camps.get_nearest_known_camp(life),
			raiders=[t['who']['life']['id'] for t in _all_targets])
	
	if combat.has_weapon(life) and _all_targets:
		if not combat.weapon_equipped_and_ready(life):
			if not 'equipping' in life:
				if combat._equip_weapon(life):
					life['equipping'] = True
			
		if _all_targets:
			_closest_target = get_closest_target(life, _all_targets)
			combat.combat(life, _closest_target['who'])
	elif _neutral_targets:
		for _ntarget in [_target['who']['life'] for _target in _neutral_targets]:
			_has_weapon = combat.get_equipped_weapons(_ntarget)
			
			if _has_weapon:
				if not speech.has_sent(life, _ntarget, 'demand_drop_item'):
					combat.disarm(life)
			else:
				if brain.get_alife_flag(life, _ntarget, 'dropped_demanded_item'):
					print 'Youre good to go!'
				else:
					print life['name'],'dadasd'
