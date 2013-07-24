from globals import *

import life as lfe

import judgement
import survival
import chunks
import sight
import brain

import logging

STATE = 'discovering'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not judgement.is_safe(life):
		return False
	
	if life['state'] in ['exploring', 'searching', 'looting', 'managing', 'finding camp', 'camping', 'working', 'visiting camp', 'needs', 'hiding']:
		brain.store_in_memory(life, 'discovery_lock', False)
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if not lfe.execute_raw(life, 'discover', 'discover_type'):
		_lost_method = lfe.execute_raw(life, 'discover', 'when_lost')
		if _lost_method:
			if not life['path'] or not brain.retrieve_from_memory(life, 'discovery_lock'):
				_explore_chunk = chunks.find_best_chunk(life, ignore_time=True, lost_method=_lost_method)
				brain.store_in_memory(life, 'discovery_lock', True)
				brain.store_in_memory(life, 'explore_chunk', _explore_chunk)
				survival.explore_known_chunks(life)
		else:
			return False
	#survival.explore_unknown_chunks(life)
	
