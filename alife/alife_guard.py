from globals import *

import life as lfe

from . import judgement
from . import movement
from . import brain

import logging

STATE = 'guarding'
TIER = TIER_COMBAT+.1

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not lfe.execute_raw(life, 'state', 'guard'):
		if life['state'] == STATE:
			lfe.clear_actions(life)
		
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_target = judgement.get_target_to_guard(life)
	
	movement.find_target(life, _target, call=False)
