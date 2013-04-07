from globals import *

import references
import judgement
import numbers
import speech
import chunks

import logging

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

def get_nearest_known_camp(life):
	_nearest_camp = {'score': -1, 'camp': None}
	
	for camp in [life['known_camps'][i] for i in life['known_camps']]:
		_key = references.find_nearest_key_in_reference(life, camp['reference'])
		_center = [int(val)+(SETTINGS['chunk size']/2) for val in _key.split(',')]
		
		_distance = numbers.distance(life['pos'], _center)
		
		if not _nearest_camp['camp'] or _distance>_nearest_camp['score']:
			_nearest_camp['camp'] = camp
			_nearest_camp['score'] = _distance
	
	return _nearest_camp['camp']

def found_camp(life, reference, announce=False):
	_camp = {'id': len(CAMPS),
		'reference': reference,
		'founder': life['id'],
		'time_founded': WORLD_INFO['ticks']}
	
	if not life['known_camps']:
		life['camp'] = _camp['id']
	
	CAMPS[_camp['id']] = _camp 
	logging.debug('%s founded camp #%s.' % (' '.join(life['name']), _camp['id']))
	discover_camp(life, _camp)
	speech.announce(life, 'share_camp_info', camp=_camp, public=True)

def unfound_camp(life, camp):
	pass

def get_all_alife_in_camp(life, camp):
	#TODO: We should write a function to do this for references, then filter the results here
	#TODO: Can we just add a is_member funtion?
	pass

def has_discovered_camp(life, camp):
	if camp['id'] in life['known_camps']:
		return True
	
	return False

def discover_camp(life, camp):
	if not life['known_camps']:
		life['camp'] = camp['id']
	life['known_camps'][camp['id']] = camp
	life['known_camps'][camp['id']]['time_discovered'] = WORLD_INFO['ticks']

	if not camp['founder'] == life['id']:
		logging.debug('%s discovered camp #%s.' % (' '.join(life['name']), camp['id']))

def is_in_camp(life, camp):
	return references.is_in_reference(life, camp['reference'])

def get_founded_camps(life):
	return [CAMPS[i] for i in CAMPS if CAMPS[i]['founder'] == life['id']]
		
