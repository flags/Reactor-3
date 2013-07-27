#TODO: THIS CAN BE IDLE BEHAVIOR

from globals import *

import life as lfe

import judgement
import survival
import chunks
import sight
import brain

import logging

STATE = 'exploring'
TIER = TIER_EXPLORE-.2

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not judgement.is_safe(life):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	_explore_chunk = chunks.find_best_chunk(life, ignore_starting=True, ignore_time=True)
	brain.store_in_memory(life, 'explore_chunk', _explore_chunk)
	
	if not _explore_chunk:
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	if survival.explore_known_chunks(life):
		return True
