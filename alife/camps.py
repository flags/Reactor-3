from globals import *

import life as lfe

import references
import judgement
import language
import survival
import movement
import numbers
import speech
import chunks
import brain
import stats
import jobs

import logging
import random

def get_camp(camp_id):
	if not camp_id in WORLD_INFO['camps']:
		raise Exception('Camp with ID \'%s\' does not exist.' % camp_id)
	
	return WORLD_INFO['camps'][camp_id]

def get_flag(life, camp_id, flag):
	if flag in life['known_camps'][camp_id]['flags']:
		return life['known_camps'][camp_id]['flags'][flag]
	
	return None

def flag(life, camp_id, flag, value):
	if not camp_id in life['known_camps']:
		raise Exception('%s does not know camp \'%s\'.' % (' '.join(life['name'])), value)
	
	life['known_camps'][camp_id]['flags'][flag] = value
	
	logging.debug('%s flagged camp \'%s\' with %s.' % (' '.join(life['name']), camp_id, flag))

def create_all_camps():
	#_best_camp = {'camp': None, 'score': 0}
	
	for camp in WORLD_INFO['reference_map']['buildings']:
		#if camp in _founded_camps:
		#	continue
		
		WORLD_INFO['camps'][str(WORLD_INFO['campid'])] = {'id': str(WORLD_INFO['campid']),
		                                                  'reference': camp,
		                                                  'groups': {}}
		WORLD_INFO['campid'] += 1
		
		#if ignore_fully_explored and len(camp) == len(references.get_known_chunks_in_reference(life, camp)):
		#	continue

def discover_camp(life, camp_id):
	_camp = {'id': camp_id,
	         'snapshot': {'time': -1, 'life': []}}
	
	life['known_camps'][camp_id] = _camp

#def find_nearest_unfounded_camp(life):
#	_founded_camps = [CAMPS[camp]['reference'] for camp in CAMPS]
#	_nearest_building = references.find_nearest_building(life, ignore_array=_founded_camps)
#	
#	return _nearest_building['reference']

def _get_nearest_known_camp(life):
	_nearest_camp = {'camp': None, 'score': -1}
	
	for camp in [life['known_camps'][i] for i in life['known_camps']]:
		_key = references.find_nearest_key_in_reference(life, get_camp(camp['id'])['reference'])
		_center = [int(val)+(WORLD_INFO['chunk_size']/2) for val in _key.split(',')]
		
		_distance = numbers.distance(life['pos'], _center)
		
		if not _nearest_camp['camp'] or _distance>_nearest_camp['score']:
			_nearest_camp['camp'] = camp
			_nearest_camp['score'] = _distance
	
	return _nearest_camp

def get_nearest_known_camp(life):
	return _get_nearest_known_camp(life)['camp']

def get_distance_to_nearest_known_camp(life):
	return _get_nearest_known_camp(life)['score']

def get_camp_via_reference(reference):
	for camp in CAMPS.values():
		if camp['reference'] == reference:
			return camp['id']
	
	return None

def get_controlling_groups(camp_id):
	_groups = {}
	
	for life in [LIFE[l] for l in get_all_alife_in_camp(camp_id)]:
		if not life['group']:
			continue
		
		if life['group'] in _groups:
			_groups[life['group']]['score'] += 1
		else:
			_groups[life['group']] = {'score': 1, 'id': life['group']}
	
	return _groups

def get_controlling_group_global(camp_id):
	_groups = get_controlling_groups(camp_id)
	_groups_controlling = [_grp['id'] for _grp in _groups.values() if _grp['score'] == max([_grp['score'] for _grp in _groups.values()])]
	if _groups_controlling:
		return _groups_controlling[0]
	
	return None

def get_controlling_group_according_to(life, camp_id):
	_best_group = {'group': None, 'score': 0}
	_camp = life['known_camps'][camp_id]
	
	for group in _camp['snapshot']['groups']:
		if not _best_group['group'] or _camp['snapshot']['groups'][group] > _best_group['score']:
			_best_group['group'] = group
			_best_group['score'] = _best_group['score']
	
	return _best_group['group']		

def get_all_alife_in_camp(camp_id):
	return [life['id'] for life in LIFE.values() if is_in_camp(life, WORLD_INFO['camps'][camp_id])]

def is_in_camp(life, camp):
	return references.life_is_in_reference(life, camp['reference'])

def is_in_any_camp(position):
	for camp in WORLD_INFO['camps'].values():
		if references.is_in_reference(position, camp['reference']):
			return camp['id']
	
	return False

def position_is_in_camp(position, camp_id):
	return references.is_in_reference(position, get_camp(camp_id)['reference'])

def get_nearest_position_in_camp(life, camp):
	_camp = WORLD_INFO['camps'][camp]
	_key = references.find_nearest_key_in_reference_exact(life['pos'], _camp['reference'])
	
	return chunks.get_nearest_position_in_chunk(life['pos'], _key)

def guard_camp(life):
	_delay = random.randint(25, jobs.get_job_detail(life['job'], 'pause'))
	
	if not life['path'] and not lfe.find_action(life, matches=[{'action': 'move'}]):
		_chunk = WORLD_INFO['chunk_map'][references.find_least_populated_key_in_reference(life, CAMPS[life['camp']]['reference'])]
		lfe.add_action(life,{'action': 'move',
			'to': random.choice(_chunk['ground'])},
			200,
			delay=_delay)
	
	return False

#def get_camp_jobs(camp_id):
#	_jobs = []
#	camp = CAMPS[camp_id]
#	
#	_j = jobs.create_job(LIFE[camp['founder']], 'guard camp', description='Guard the camp.')
#	jobs.add_detail_to_job(_j, 'camp', camp_id)
#	jobs.add_detail_to_job(_j, 'pause', 90)
#	jobs.add_job_task(_j, 'guard', callback=guard_camp, required=True)
#	_jobs.append(_j)
#	
#	#_j = jobs.create_job(LIFE[camp['founder']], 'scout', description='Scout the area.')
#	#jobs.add_detail_to_job(_j, 'camp', camp_id)
#	#jobs.add_job_task(_j, 'explore', callback=survival._job_explore_unknown_chunks, required=True)
#	#_jobs.append(_j)
#	
#	return _jobs
