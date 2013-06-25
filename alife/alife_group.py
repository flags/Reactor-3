from globals import *

import judgement
import groups
import stats

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	#if not life['group'] or not life['id'] == groups.get_group(life['group'])['leader']:
	#	return False
	
	return RETURN_SKIP

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if life['group'] and life['id'] == groups.get_group(life['group'])['leader']:
		if stats.desires_camp(life):
			print 'CAMP DUDE!'
			