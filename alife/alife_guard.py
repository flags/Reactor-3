from globals import *

import life as lfe

import judgement
import movement
import brain

import logging

STATE = 'follow'
TIER = TIER_EXPLORE-.2

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not lfe.execute_raw(life, 'state', 'follow'):
		if life['state'] == STATE:
			lfe.clear_actions(life)
		
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	movement.find_target(life, judgement.get_target_to_follow(life), call=False)
