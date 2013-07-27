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
TIER = TIER_COMBAT-.3

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
	
	if not lfe.execute_raw(life, 'combat', 'ranged') and not lfe.execute_raw(life, 'combat', 'melee'):
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
	
	if lfe.execute_raw(life, 'combat', 'ranged_ready', break_on_true=True, break_on_false=False):
		_closest_target = get_closest_target(life, _all_targets)
		combat.ranged_combat(life, _closest_target)

	if lfe.execute_raw(life, 'combat', 'melee_ready', break_on_true=True, break_on_false=False):
		_closest_target = get_closest_target(life, _all_targets)
		combat.melee_combat(life, _closest_target)