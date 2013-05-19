from globals import *

import life as lfe

import references
import judgement
import language
import numbers
import speech
import chunks
import jobs

import logging
import random

def find_nearest_unfounded_camp(life):
	_founded_camps = [CAMPS[camp]['reference'] for camp in CAMPS]
	_nearest_building = references.find_nearest_building(life, ignore_array=_founded_camps)
	
	return _nearest_building['reference']

def find_best_unfounded_camp(life):
	_founded_camps = [CAMPS[camp]['reference'] for camp in CAMPS]
	
	_best_camp = {'camp': None, 'score': 4}
	for camp in REFERENCE_MAP['buildings']:
		if camp in _founded_camps:
			continue
	
		_score = judgement.judge_camp(life, camp)
		if _score>_best_camp['score']:
			_best_camp['camp'] = camp
			_best_camp['score'] = _score
	
	return _best_camp['camp']

def _get_nearest_known_camp(life):
	_nearest_camp = {'score': -1, 'camp': None}
	
	for camp in [life['known_camps'][i] for i in life['known_camps']]:
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

def found_camp(life, reference, announce=False):
	_camp = {'id': len(CAMPS)+1,
		'name': language.generate_place_name(),
		'reference': reference,
		'founder': life['id'],
		'time_founded': WORLD_INFO['ticks'],
		'info': {'population': 0},
		'stats': {}}
	
	if not life['known_camps']:
		life['camp'] = _camp['id']
	
	CAMPS[_camp['id']] = _camp 
	logging.debug('%s founded camp #%s.' % (' '.join(life['name']), _camp['id']))
	discover_camp(life, _camp)
	speech.announce(life, 'share_camp_info', camp=_camp, founder=life['id'], public=False)

def unfound_camp(life, camp):
	pass

def get_all_alife_in_camp(life, camp):
	#TODO: We should write a function to do this for references, then filter the results here
	#TODO: Can we just add a is_member funtion?
	pass

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
		_chunk = CHUNK_MAP[references.find_least_controlled_key_in_reference(life, CAMPS[life['camp']]['reference'])]
		lfe.add_action(life,{'action': 'move',
			'to': random.choice(_chunk['ground'])},
			200,
			delay=_delay)
	return False

def get_camp_jobs(camp_id):
	_jobs = []
	camp = CAMPS[camp_id]
	
	_j = jobs.create_job(LIFE[camp['founder']], 'guard camp')
	jobs.add_detail_to_job(_j, 'camp', camp_id)
	jobs.add_detail_to_job(_j, 'pause', 90)
	jobs.add_job_task(_j, 'guard', callback=guard_camp, required=True)
	
	_jobs.append(_j)
	return _jobs
