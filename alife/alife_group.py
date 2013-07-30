from globals import *

import judgement
import movement
import groups
import speech
import brain
import stats
import jobs

TIER = TIER_PASSIVE

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	return RETURN_SKIP

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if not life['group']:
		if stats.desires_to_create_group(life):
			groups.create_group(life)
		
		return False
	
	_group = groups.get_group(life['group'])
	
	if _group['leader'] == life['id']:
		if stats.wants_to_abandon_group(life, life['group']):
			print 'ABANDONING ON THESE TERMS' * 10
			return False
		
		if stats.desires_shelter(life):
			if not groups.get_shelter(life['group']):
				groups.find_shelter(life, life['group'])
			
	
	#elif brain.get_alife_flag(life, _group['leader'], 'follow'):
	#	#TODO: Get this over to alife_explore?
		
	