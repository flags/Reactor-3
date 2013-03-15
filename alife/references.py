from globals import *

import life as lfe

import judgement
import maps

import numbers

def _find_nearest_reference(life, ref_type, skip_current=False, skip_known=False):
	_lowest = {'chunk_key': None, 'reference': None, 'distance': -1}
	
	for reference in REFERENCE_MAP[ref_type]:
		_nearest_key = find_nearest_key_in_reference(life, reference)

		if skip_current and maps.get_chunk(_nearest_key) == lfe.get_current_chunk(life):
			continue
			
		if skip_known and _nearest_key in life['known_chunks']:
			continue

		_center = [int(val)+(SETTINGS['chunk size']/2) for val in _nearest_key.split(',')]
		_distance = numbers.distance(life['pos'], _center)
		
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _nearest_key
			_lowest['reference'] = reference
	
	return _lowest

def _find_best_reference(life, ref_type):
	_best_reference = {'reference': None, 'score': -1}
	
	for reference in REFERENCE_MAP[ref_type]:
		_score = judgement.judge_reference(life, reference, ref_type)
		
		if not _score:
			continue
		
		#TODO: We do this twice (check in path_along_reference). Not good!
		if numbers.distance(life['pos'],
			maps.get_chunk(find_nearest_key_in_reference(life, reference))['pos'])/SETTINGS['chunk size']>10:
			
			#print find_nearest_key_in_reference(life, reference),numbers.distance(life['pos'],
			#	maps.get_chunk(find_nearest_key_in_reference(life, reference))['pos'])/SETTINGS['chunk size']
			#pass
			continue
		
		
		if not _best_reference['reference'] or _score>_best_reference['score']:
			_best_reference['score'] = _score
			_best_reference['reference'] = reference
	
	return _best_reference

def find_nearest_key_in_reference(life, reference):
	_lowest = {'chunk_key': None, 'distance': -1}

	for _key in reference:
		_center = [int(val)+(SETTINGS['chunk size']/2) for val in _key.split(',')]
		_distance = numbers.distance(life['pos'], _center)
			
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _key
	
	return _lowest['chunk_key']

def path_along_reference(life, ref_type):
	_best_reference = _find_best_reference(life, ref_type)['reference']

	if not _best_reference:
		return False

	_starting_chunk_key = find_nearest_key_in_reference(life, _best_reference)
	_starting_chunk = maps.get_chunk(_starting_chunk_key)
	_chunk_path_keys = []
	SELECTED_TILES[0] = []
	_directions = {}
	
	for neighbor_key in _starting_chunk['neighbors']:
		if maps.get_chunk(neighbor_key) == lfe.get_current_chunk(life):
			continue
		
		_neighbor_pos = [int(val)+(SETTINGS['chunk size']/2) for val in neighbor_key.split(',')]
		_cent = (lfe.get_current_chunk(life)['pos'][0]+(SETTINGS['chunk size']/2),
			lfe.get_current_chunk(life)['pos'][1]+(SETTINGS['chunk size']/2))
		_neighbor_direction = numbers.direction_to(_cent, _neighbor_pos)
		_directions[_neighbor_direction] = {'key': neighbor_key, 'score': 9999}
		
		SELECTED_TILES[0].append((_cent[0],
			_cent[1],2))
	
	_best_dir = {'dir': -1, 'score': 0}
	for mod in range(-45, 361, 45):
		_new_dir = life['discover_direction']+mod
		
		if _new_dir>=360:
			_new_dir -= 360
		
		if _new_dir in _directions:
			_score = len(maps.get_chunk(_directions[_new_dir]['key'])['neighbors'])
			
			if _directions[_new_dir]['key'] in life['known_chunks']:
				_last_visit_score = 0#(WORLD_INFO['ticks']-life['known_chunks'][_directions[_new_dir]['key']]['last_visited'])/FPS
			else:
				_last_visit_score = WORLD_INFO['ticks']/FPS
			
			if not _last_visit_score:
				continue
			
			if _score>_best_dir['score']:
				_best_dir['dir'] = _new_dir
				_best_dir['score'] = _score

	if _best_dir['dir'] == -1:
		return None
	
	life['discover_direction'] = _best_dir['dir']
	return _directions[_best_dir['dir']]['key']

def find_nearest_road(life):
	_best_reference = _find_best_reference(life, 'roads')['reference']
	
	if _best_reference:
		return _best_reference
	
	return _find_nearest_reference(life, 'roads')['reference']

def find_nearest_building(life):
	return _find_best_reference(life, 'buildings')
