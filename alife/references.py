from globals import *

import life as lfe

from . import judgement
import mapgen
from . import chunks
import alife
import maps

import bad_numbers

def get_reference(reference_id):
	return WORLD_INFO['references'][reference_id]

def _find_nearest_reference(life, ref_type, skip_current=False, skip_known=False, skip_unknown=False, ignore_array=[]):
	_lowest = {'chunk_key': None, 'reference': None, 'distance': -1}
	
	for reference in WORLD_INFO['reference_map'][ref_type]:
		if reference in ignore_array:
			continue
		
		_nearest_key = find_nearest_key_in_reference(life, reference)

		if skip_current and maps.get_chunk(_nearest_key) == lfe.get_current_chunk(life):
			continue
			
		if skip_known and _nearest_key in life['known_chunks']:
			continue

		if skip_unknown and not _nearest_key in life['known_chunks']:
			continue

		_center = [int(val)+(WORLD_INFO['chunk_size']//2) for val in _nearest_key.split(',')]
		_distance = bad_numbers.distance(life['pos'], _center)
		
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _nearest_key
			_lowest['reference'] = reference
	
	return _lowest

def _find_nearest_reference_exact(position, ref_type=None):
	_lowest = {'chunk_key': None, 'reference': None, 'distance': -1}
	
	for _r_type in WORLD_INFO['reference_map']:
		if ref_type and not _r_type == ref_type:
			continue
		
		for reference in WORLD_INFO['reference_map'][_r_type]:
			_center = [int(val)+(WORLD_INFO['chunk_size']//2) for val in _nearest_key.split(',')]
			_distance = bad_numbers.distance(position, _center)
			_nearest_key = find_nearest_key_in_reference_exact(position, reference)
			
			if not _lowest['chunk_key'] or _distance<_lowest['distance']:
				_lowest['distance'] = _distance
				_lowest['chunk_key'] = _nearest_key
				_lowest['reference'] = reference
	
	return _lowest

def _find_nearest_reference_type_exact(position, ref_type=None):
	_lowest = {'chunk_key': None, 'reference': None, 'distance': -1}
	
	for chunk_keys in WORLD_INFO['refs'][ref_type]:
		_nearest_chunk_key = chunks.get_nearest_chunk_in_list(position, chunk_keys)
		_center = [int(val)+(WORLD_INFO['chunk_size']//2) for val in _nearest_chunk_key.split(',')]
		_distance = bad_numbers.distance(position, _center)
		
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _nearest_chunk_key
			_lowest['chunk_keys'] = chunk_keys
	
	return _lowest

def _find_best_unknown_reference(life, ref_type):
	_best_reference = {'reference': None, 'score': -1}
	
	for reference in WORLD_INFO['reference_map'][ref_type]:
		_score = judgement.judge_reference(life, reference, known_penalty=True)
		
		if not _score:
			continue
		
		_chunk_key = find_nearest_key_in_reference(life, reference)
		
		if bad_numbers.distance(life['pos'], maps.get_chunk(_chunk_key)['pos'])//WORLD_INFO['chunk_size']>10:
			continue
		
		if not _best_reference['reference'] or _score>_best_reference['score']:
			_best_reference['score'] = _score
			_best_reference['reference'] = reference
			_best_reference['chunk_key'] = _chunk_key
	
	return _best_reference

def find_nearest_reference_of_type(pos, reference_type):
	return _find_nearest_reference_type_exact(pos, reference_type)

def find_nearest_chunk_key_in_reference_of_type(life, reference_type):
	return find_nearest_reference_of_type(life['pos'], reference_type)['chunk_key']

def find_nearest_key_in_reference(life, reference_id, unknown=False, ignore_current=False, threshold=-1):
	_lowest = {'chunk_key': None, 'distance': 9000}

	#Dirty hack here...
	#We can use the list of visible chunks to find the nearest key in the reference
	#This is actually SLOWER if the NPC can't see any keys in the reference and a search
	#has to be done (the way we're doing it now.)
	
	_reference = get_reference(reference_id)
	
	for _key in _reference:
		if unknown and _key in life['known_chunks']:
			continue
		
		if ignore_current and lfe.get_current_chunk_id(life) == _key:
			print('ignoring current')
			continue
		
		if not maps.get_chunk(_key)['ground']:
			continue
		
		_center = [int(val)+(WORLD_INFO['chunk_size']//2) for val in _key.split(',')]
		_distance = bad_numbers.distance(life['pos'], _center)
		
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _key
		
		if threshold > -1 and _lowest['distance'] <= threshold:
			break
	
	return _lowest['chunk_key']

def find_nearest_key_in_reference_exact(position, reference):
	_lowest = {'chunk_key': None, 'distance': 100}

	for _key in reference:		
		if not maps.get_chunk(_key)['ground']:
			continue
		
		_center = [int(val)+(WORLD_INFO['chunk_size']//2) for val in _key.split(',')]
		_distance = bad_numbers.distance(position, _center)
		
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _key
	
	return _lowest['chunk_key']

def find_least_populated_key_in_reference(life, reference):
	_lowest = {'chunk_key': None, 'score': 0}
	
	for _key in reference:
		_chunk = maps.get_chunk(_key)
		_score = len(_chunk['life'])
		
		if chunks.is_in_chunk(life, _key) and _score == 1:
			_score = -1
		
		if not _lowest['chunk_key'] or _score<_lowest['score']:
			_lowest['chunk_key'] = _key
			_lowest['score'] = _score
		
		if _score == -1:
			break
	
	return _lowest['chunk_key']

def path_along_reference(life, ref_type):
	_reference = WORLD_INFO['references'][WORLD_INFO['reference_map']['roads'][0]]
	_visible_chunks = alife.brain.get_flag(life, 'visible_chunks')
	_starting_chunk_key = alife.chunks.get_nearest_chunk_in_list(life['pos'], _reference, check_these_chunks_first=_visible_chunks)
	_chunk_path_keys = []
	_directions = {}
	
	for neighbor_key in mapgen.get_neighbors_of_type(WORLD_INFO, _starting_chunk_key, ref_type, diagonal=True):
		if maps.get_chunk(neighbor_key) == lfe.get_current_chunk(life):
			continue
		
		_neighbor_pos = [int(val)+(WORLD_INFO['chunk_size']//2) for val in neighbor_key.split(',')]
		_cent = (lfe.get_current_chunk(life)['pos'][0]+(WORLD_INFO['chunk_size']//2),
			lfe.get_current_chunk(life)['pos'][1]+(WORLD_INFO['chunk_size']//2))
		_neighbor_direction = bad_numbers.direction_to(_cent, _neighbor_pos)
		_directions[_neighbor_direction] = {'key': neighbor_key, 'score': 9999}
	
	_best_dir = {'dir': -1, 'score': 0}
	for mod in range(-45, 361, 45):
		_new_dir = life['discover_direction']+mod
		
		if _new_dir>=360:
			_new_dir -= 360
		
		if _new_dir in _directions:
			_score = 0
			
			if _directions[_new_dir]['key'] in life['known_chunks']:
				continue
			
			_score += (180-(abs(_new_dir-life['discover_direction'])))//45
			_score += life['discover_direction_history'].count(_new_dir)
			
			if _score>=_best_dir['score']:
				if _score==_best_dir['score']:
					_chunk = maps.get_chunk(_directions[_new_dir]['key'])
				
				_best_dir['dir'] = _new_dir
				_best_dir['score'] = _score

	if _best_dir['dir'] == -1:
		return None
	
	#print _best_dir,_directions[_best_dir['dir']]
	
	life['discover_direction_history'].append(life['discover_direction'])
	if len(life['discover_direction_history'])>=5:
		life['discover_direction_history'].pop(0)
	
	life['discover_direction'] = _best_dir['dir']
	return _directions[_best_dir['dir']]['key']

def is_in_reference(position, reference):
	for chunk_key in reference:
		if chunks.position_is_in_chunk(position, chunk_key):
			return True
	
	return False

def is_in_any_reference(position):
	for r_type in WORLD_INFO['reference_map']:
		for reference in WORLD_INFO['reference_map'][r_type]:
			if is_in_reference(position, get_reference(reference)):
				return reference
	
	return False

def life_is_in_reference(life, reference):
	return is_in_reference(life['pos'], reference)

def get_known_chunks_in_reference(life, reference):
	_known_chunks = []
	for _chunk_key in reference:
		if not _chunk_key in life['known_chunks']:
			continue
		
		_known_chunks.append(_chunk_key)
	
	return _known_chunks

def find_nearest_road(position, skip_unknown=True, ignore_array=[]):
	
	return _find_nearest_reference_exact(position, 'roads')

def find_nearest_building(life, skip_unknown=True, ignore_array=[]):
	return _find_nearest_reference(life, 'buildings', skip_unknown=skip_unknown, ignore_array=ignore_array)

def get_alife_in_reference_matching(reference_id, matching):
	_life = []
	for chunk_key in get_reference(reference_id):
		_life.extend(chunks.get_alife_in_chunk_matching(chunk_key, matching))
	
	return _life
