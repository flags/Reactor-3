from globals import *

import life as lfe

import judgement
import movement
import groups
import speech
import action
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
			_group_id = groups.create_group(life)
			_group = groups.get_group(_group_id)
			_pos = lfe.get_current_chunk(life)['pos']
			
			_j = jobs.create_job(life, 'Gather',
			                     gist='create_group',
			                     description='Gathering new group %s at %s, %s.' % (_group_id, _pos[0], _pos[1]))
		
			jobs.add_task(_j, '0', 'move_to_chunk',
				          action.make_small_script(function='travel_to_position',
				                                   kwargs={'pos': _pos}),
				          delete_on_finish=False)
			jobs.add_task(_j, '1', 'talk',
				          action.make_small_script(function='start_dialog',
				                                   kwargs={'target': life['id'], 'gist': 'form_group'}),
				          requires=['0'],
				          delete_on_finish=False)
			
			groups.flag(_group_id, 'job_gather', _j)
			
			groups.announce(life, _group_id, 'job', 'New group gathering.', consider_motive=True, job_id=_j)
		
		return False
	
	if groups.is_leader(life['group'], life['id']):
		#TODO: Re-announce group from time to time LOGICALLY
		if groups.get_group(life['group'])['claimed_motive'] == 'survival' and lfe.ticker(life, 'announce_group', 200):
			_job_id = groups.get_flag(life['group'], 'job_gather')
			groups.announce(life, life['group'], 'job', 'New group gathering.', consider_motive=True, job_id=_job_id)
	
	_group = groups.get_group(life['group'])
	
	if _group['leader'] == life['id']:
		if stats.wants_to_abandon_group(life, life['group']):
			print 'ABANDONING ON THESE TERMS' * 10
			return False
		
		groups.process_events(life['group'])
	