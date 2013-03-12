from globals import *

import life as lfe

import maps

import numbers

def _find_nearest_reference(life, ref_type, skip_current=False):
	_lowest = {'chunk_key': None, 'reference': None, 'distance': -1}
	for reference in REFERENCE_MAP[ref_type]:
		for _key in reference:
			if skip_current and maps.get_chunk(_key) == lfe.get_current_chunk(life):
				continue
			
			_center = [int(val)+SETTINGS['chunk size'] for val in _key.split(',')]
			_distance = numbers.distance(life['pos'], _center)
			
			if not _lowest['chunk_key'] or _distance<_lowest['distance']:
				_lowest['distance'] = _distance
				_lowest['chunk_key'] = _key
				_lowest['reference'] = reference
	
	return _lowest

def path_along_reference(life, ref_type):
	_starting_chunk_key = _find_nearest_reference(life, ref_type)['chunk_key']
	_starting_chunk = maps.get_chunk(_starting_chunk_key)
	_chunk_path_keys = []
	
	_directions = {}
	SELECTED_TILES[0] = []
	for neighbor_key in _starting_chunk['neighbors']:
		_neighbor_pos = [int(val) for val in neighbor_key.split(',')]
		if maps.get_chunk(neighbor_key) == lfe.get_current_chunk(life):
			continue
		
		_cent = (lfe.get_current_chunk(life)['pos'][0]+(SETTINGS['chunk size']/2),
			lfe.get_current_chunk(life)['pos'][1]+(SETTINGS['chunk size']/2))
		_neighbor_direction = numbers.direction_to(_cent, _neighbor_pos)
		_directions[_neighbor_direction] = neighbor_key
		
		SELECTED_TILES[0].append((_cent[0],_cent[1],2))
	
	for mod in [-45, 0, 45]:
		_new_dir = life['discover_direction']+mod
		
		if _new_dir>=360:
			_new_dir -= 360
		
		if _new_dir in _directions:
			life['discover_direction'] = _new_dir
			return _directions[_new_dir]
		
	return None

def find_nearest_road(life):
	return _find_nearest_reference(life, 'roads')['reference']

def find_nearest_building(life):
	return _find_nearest_reference(life, 'buildings')
