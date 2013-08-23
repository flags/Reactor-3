from globals import *

import life as lfe

import judgement
import survival
import chunks
import sight
import brain
import smp

import logging

STATE = 'discovering'
TIER = TIER_EXPLORE-.1

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if brain.get_flag(life, 'lost'):
		if STATE in life['states']:
			return False
		else:
			brain.unflag(life, 'lost')
		
		print life['name'],'lost'
	
	if not judgement.is_safe(life):
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
				if not 'scanned_chunks' in life['state_flags']:
					life['state_flags']['scanned_chunks'] = []
				
				if SETTINGS['smp']:
					sight.scan_surroundings(life, _chunks=brain.get_flag(life, 'nearby_chunks'), ignore_chunks=life['state_flags']['scanned_chunks'])
				else:
					sight.scan_surroundings(life, ignore_chunks=life['state_flags']['scanned_chunks'])
				
				_explore_chunk = chunks.find_best_chunk(life, ignore_starting=True, ignore_time=True, lost_method=_lost_method, only_recent=True)
				brain.store_in_memory(life, 'discovery_lock', True)
				brain.store_in_memory(life, 'explore_chunk', _explore_chunk)
				
				if not _explore_chunk:
					print life['name'],'is lost'
					brain.flag(life, 'lost')
					return False
				
				survival.explore_known_chunks(life)
		else:
			return False
