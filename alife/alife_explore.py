from globals import *

import life as lfe

import judgement
import survival
import chunks
import sight

import logging

STATE = 'exploring'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] in ['looting', 'finding camp', 'camping', 'needs', 'working']:
		return False
	
	if not judgement.is_safe(life):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if not chunks.find_best_known_chunk(life):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	survival.explore_known_chunks(life)
	
