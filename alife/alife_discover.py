from globals import *

import life as lfe

import judgement
import survival
import chunks
import sight

import logging

STATE = 'discovering'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not judgement.is_safe(life):
		return False
	
	if life['state'] in ['exploring', 'looting', 'managing', 'finding camp', 'camping', 'working', 'visiting camp', 'needs', 'hiding']:
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if not lfe.execute_raw(life, 'discover', 'discover_type'):
		return False
	#survival.explore_unknown_chunks(life)
	
