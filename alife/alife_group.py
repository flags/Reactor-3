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
		return False
	
	_group = groups.get_group(life['group'])
	
	if _group['leader'] == life['id']:
		if stats.desires_to_create_camp(life) and groups.is_ready_to_camp(life['group']):
			speech.announce(life, 'follow', group=life['group'])
		
		if stats.wants_to_abandon_group(life, life['group']):
			print 'ABANDONING ON THESE TERMS' * 10
			
	
	#elif brain.get_alife_flag(life, _group['leader'], 'follow'):
	#	#TODO: Get this over to alife_explore?
		
	