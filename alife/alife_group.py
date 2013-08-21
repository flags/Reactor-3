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
			
			_j = jobs.create_job(life, 'Gather', gist='create_group', description='Gather for new group.')
		
			jobs.add_task(_j, '0', 'move_to_chunk',
				          action.make_small_script(function='travel_to_position',
				                                   kwargs={'pos': lfe.get_current_chunk(life)['pos']}),
				          delete_on_finish=True)
			jobs.add_task(_j, '1', 'talk',
				          action.make_small_script(function='start_dialog',
				                                   kwargs={'target': life['id'], 'gist': 'form_group'}),
				          requires=['0'],
				          delete_on_finish=True)
			
			groups.flag(_group_id, 'job_gather', _j)
			
			if _group['claimed_motive'] == 'wealth':
				_announce_to = LIFE.keys()
				_announce_to.remove(life['id'])
			elif _group['claimed_motive'] == 'crime':
				_announce_to = judgement.get_trusted(life, visible=False)
			elif _group['claimed_motive'] == 'survival':
				_announce_to = LIFE.keys()
				_announce_to.remove(life['id'])
			#TODO: Could have an option here to form an emergency "combat" group
			
			for life_id in _announce_to:
				speech.communicate(life,
						       'job',
						       msg='New group gather at xx,yy',
						       matches=[{'id': life_id}],
						       job_id=_j)
		
		return False
	
	_group = groups.get_group(life['group'])
	
	if _group['leader'] == life['id']:
		if stats.wants_to_abandon_group(life, life['group']):
			print 'ABANDONING ON THESE TERMS' * 10
			return False
		
		groups.process_events(life['group'])
	