from globals import *

import life as lfe

import judgement
import movement
import numbers
import sight
import brain

import logging

STATE = 'cover'
TIER = TIER_COMBAT-.5

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not lfe.execute_raw(life, 'state', 'cover'):
		if life['state'] == STATE:
			lfe.clear_actions(life)
			
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_threats = judgement.get_combat_targets(life, recent_only=True, ignore_escaped=2)
	
	for target in [LIFE[t] for t in _threats]:
		if numbers.distance(life['pos'], brain.knows_alife(life, target)['last_seen_at']) >= sight.get_vision(life):
			_threats.remove(target['id'])
	
	movement.escape(life, _threats)
