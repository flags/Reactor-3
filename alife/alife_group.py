from globals import *

import judgement
import movement
import groups
import speech
import brain
import stats
import jobs

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
			print '*' * 10, life['group']
			
			#DEAD: Following via jobs system
			#_j = jobs.create_job(life, 'follow to camp')
			#jobs.add_detail_to_job(_j, 'target', life['id'])
			#
			#for i in range(len(groups.get_group(life['group'])['members'])):
			#	jobs.add_job_task(_j, 'follow alife (%s)' % i, callback=movement.follow_alife, required=True)
			#
			#groups.assign_job(life, life['group'], _j)
			#jobs.process_job(_j)
	
	#elif brain.get_alife_flag(life, _group['leader'], 'follow'):
	#	#TODO: Get this over to alife_explore?
		
	