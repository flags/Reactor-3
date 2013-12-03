from globals import *

import life as lfe

import judgement
import movement
import numbers
import speech
import camps
import brain
import jobs

import logging

STATE = 'searching'
TIER = TIER_COMBAT

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	_lost_targets = judgement.get_combat_targets(life, escaped_only=True)
	brain.store_in_memory(life, 'lost_targets', _lost_targets)
	
	if not _lost_targets:
		return False
	else:
		print life['name'], _lost_targets
	
	return RETURN_VALUE

def tick(life):
	_lost_targets = judgement.get_threats(life, escaped_only=True, ignore_escaped=2)
	
	movement.search_for_target(life, _lost_targets[0])