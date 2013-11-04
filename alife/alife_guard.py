from globals import *

import life as lfe

import judgement
import movement
import brain

import logging

STATE = 'guarding'
TIER = TIER_COMBAT+.1

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not lfe.execute_raw(life, 'state', 'guard'):
		print life['name'],'nobody'
		if life['state'] == STATE:
			lfe.clear_actions(life)
		
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_surrendering_targets = judgement.get_combat_targets(life, ignore_escaped=True, filter_func=lambda life, life_id: LIFE[life_id]['state'] == 'surrender')
	_target = judgement.get_nearest_target_in_list(life, _surrendering_targets)['target_id']
	print _target
	movement.find_target(life, _target, call=False)
