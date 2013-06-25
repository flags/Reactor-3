from globals import *

import judgement
import movement
import groups
import stats
import jobs

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	return RETURN_SKIP

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if life['group'] and life['id'] == groups.get_group(life['group'])['leader']:
		if stats.desires_camp(life) and groups.is_ready_to_camp(life['group']):
			_j = jobs.create_job(life, 'give information')
			jobs.add_detail_to_job(_j, 'target', life['id'])
			
			for i in range(len(groups.get_group(life['group'])['members'])):
				jobs.add_job_task(_j, 'follow alife (%s)' % i, callback=movement.follow_alife, required=True)
			
			groups.assign_job(life, life['group'], _j)
			jobs.process_job(_j)
	
	#groups.distribute(life, 'follow', who=life['id'])