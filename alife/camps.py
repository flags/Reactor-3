from globals import *

import life as lfe

import references
import judgement
import language
import survival
import numbers
import speech
import chunks
import stats
import jobs

import logging
import random

def find_nearest_unfounded_camp(life):
	_founded_camps = [CAMPS[camp]['reference'] for camp in CAMPS]
	_nearest_building = references.find_nearest_building(life, ignore_array=_founded_camps)
	
	return _nearest_building['reference']

def find_best_unfounded_camp(life, ignore_fully_explored=False):
	_founded_camps = [CAMPS[camp]['reference'] for camp in CAMPS]
	
	_best_camp = {'camp': None, 'score': 0}
	for camp in WORLD_INFO['reference_map']['buildings']:
		if camp in _founded_camps:
			continue
		
		if ignore_fully_explored and len(camp) == len(references.get_known_chunks_in_reference(life, camp)):
			continue
	
		_score = judgement.judge_camp(life, camp)
		if _score>_best_camp['score']:
			_best_camp['camp'] = camp
			_best_camp['score'] = _score
	
	return _best_camp

def _get_nearest_known_camp(life):
	_nearest_camp = {'camp': None, 'score': -1}
	
	for camp in [life['known_camps'][i] for i in life['known_camps']]:
		if lfe.get_memory(life, matches={'camp': camp, 'text': 'denied from camp'}):
			continue
		
		_key = references.find_nearest_key_in_reference(life, camp['reference'])
		_center = [int(val)+(SETTINGS['chunk size']/2) for val in _key.split(',')]
		
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

def get_camp(camp_id):
	if not camp_id in CAMPS:
		raise Exception('Camp with ID \'%s\' does not exist.' % camp_id)
	
	return CAMPS[camp_id]

def found_camp(life, reference, announce=False):
	_camp = {'id': len(CAMPS)+1,
		'name': language.generate_place_name(),
		'reference': reference,
		'founder': life['id'],
		'time_founded': WORLD_INFO['ticks'],
		'info': {'population': 0},
		'stats': {},
		'raid': {}}
	
	if not life['known_camps']:
		life['camp'] = _camp['id']
	
	CAMPS[_camp['id']] = _camp 
	lfe.memory(life, 'founded camp', camp=_camp['id'])
	logging.debug('%s founded camp #%s.' % (' '.join(life['name']), _camp['id']))
	discover_camp(life, _camp)
	speech.announce(life, 'share_camp_info', camp=_camp, founder=life['id'], public=False)

def unfound_camp(life, camp):
	pass

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

def get_controlling_group(camp_id):
	_groups = get_controlling_groups(camp_id)
	
	return [_grp['id'] for _grp in _groups.values() if _grp['score'] == max([_grp['score'] for _grp in _groups.values()])]

def get_all_alife_in_camp(camp_id):
	return [life['id'] for life in LIFE.values() if is_in_camp(life, CAMPS[camp_id])]

def has_discovered_camp(life, camp):
	if camp in life['known_camps']:
		return True
	
	return False

def discover_camp(life, camp):
	if not life['known_camps']:
		life['camp'] = camp['id']
	life['known_camps'][camp['id']] = camp.copy()
	life['known_camps'][camp['id']]['time_discovered'] = WORLD_INFO['ticks']

	if not camp['founder'] == life['id']:
		logging.debug('%s discovered camp #%s.' % (' '.join(life['name']), camp['id']))

def is_in_camp(life, camp):
	return references.life_is_in_reference(life, camp['reference'])

def is_in_any_camp(position):
	for camp in CAMPS.values():
		if references.is_in_reference(position, camp['reference']):
			return camp['id']
	
	return False		

def position_is_in_camp(position, camp):
	return references.is_in_reference(position, camp['reference'])

def get_founded_camps(life):
	return [CAMPS[i] for i in CAMPS if CAMPS[i]['founder'] == life['id']]

def get_camp_info(life, camp):
	_info = {'founder': -1,
		'estimated_population': 0}
	
	if camp['id'] in [camp['id'] for camp in get_founded_camps(life)]:
		_info['founder'] = life['id']
	else:
		for founder in lfe.get_memory(life, matches={'camp': camp['id'], 'text': 'heard about camp', 'founder': '*'}):
			_info['founder'] = founder['founder']
	
	for _life in life['know'].values():
		#TODO: 300?
		if _life['last_seen_time']>=300:
			continue
		
		if position_is_in_camp(_life['last_seen_at'], camp):
			_info['estimated_population'] += 1
	
	return _info

def register_camp_info(life, camp, info):
	camp['info'].update(info)

def guard_camp(life):
	_delay = random.randint(25, jobs.get_job_detail(life['job'], 'pause'))
	
	if not life['path'] and not lfe.find_action(life, matches=[{'action': 'move'}]):
		_chunk = CHUNK_MAP[references.find_least_populated_key_in_reference(life, CAMPS[life['camp']]['reference'])]
		lfe.add_action(life,{'action': 'move',
			'to': random.choice(_chunk['ground'])},
			200,
			delay=_delay)
	
	return False

def get_camp_jobs(camp_id):
	_jobs = []
	camp = CAMPS[camp_id]
	
	_j = jobs.create_job(LIFE[camp['founder']], 'guard camp', description='Guard the camp.')
	jobs.add_detail_to_job(_j, 'camp', camp_id)
	jobs.add_detail_to_job(_j, 'pause', 90)
	jobs.add_job_task(_j, 'guard', callback=guard_camp, required=True)
	_jobs.append(_j)
	
	#_j = jobs.create_job(LIFE[camp['founder']], 'scout', description='Scout the area.')
	#jobs.add_detail_to_job(_j, 'camp', camp_id)
	#jobs.add_job_task(_j, 'explore', callback=survival._job_explore_unknown_chunks, required=True)
	#_jobs.append(_j)
	
	return _jobs
