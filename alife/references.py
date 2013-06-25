from globals import *

import life as lfe

import judgement
import chunks
import maps

import numbers

def _find_nearest_reference(life, ref_type, skip_current=False, skip_known=False, skip_unknown=False, ignore_array=[]):
	_lowest = {'chunk_key': None, 'reference': None, 'distance': -1}
	
	for reference in REFERENCE_MAP[ref_type]:
		if reference in ignore_array:
			continue
		
		_nearest_key = find_nearest_key_in_reference(life, reference)

		if skip_current and maps.get_chunk(_nearest_key) == lfe.get_current_chunk(life):
			continue
			
		if skip_known and _nearest_key in life['known_chunks']:
			continue

		if skip_unknown and not _nearest_key in life['known_chunks']:
			continue

		_center = [int(val)+(SETTINGS['chunk size']/2) for val in _nearest_key.split(',')]
		_distance = numbers.distance(life['pos'], _center)
		
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _nearest_key
			_lowest['reference'] = reference
	
	return _lowest

def _find_nearest_reference_exact(position, ref_type=None):
	_lowest = {'chunk_key': None, 'reference': None, 'distance': -1}
	
	for _r_type in REFERENCE_MAP:
		if ref_type and not _r_type == ref_type:
			continue
		
		for reference in REFERENCE_MAP[_r_type]:
			_center = [int(val)+(SETTINGS['chunk size']/2) for val in _nearest_key.split(',')]
			_distance = numbers.distance(position, _center)
			_nearest_key = find_nearest_key_in_reference_exact(position, reference)
			
			if not _lowest['chunk_key'] or _distance<_lowest['distance']:
				_lowest['distance'] = _distance
				_lowest['chunk_key'] = _nearest_key
				_lowest['reference'] = reference
	
	return _lowest

def _find_best_unknown_reference(life, ref_type):
	_best_reference = {'reference': None, 'score': -1}
	
	for reference in REFERENCE_MAP[ref_type]:
		_score = judgement.judge_reference(life, reference, ref_type, known_penalty=True)
		
		if not _score:
			continue
		
		#TODO: We do this twice (check in path_along_reference). Not good!
		if numbers.distance(life['pos'],
			maps.get_chunk(find_nearest_key_in_reference(life, reference))['pos'])/SETTINGS['chunk size']>10:
			continue
		
		if not _best_reference['reference'] or _score>_best_reference['score']:
			_best_reference['score'] = _score
			_best_reference['reference'] = reference
	
	return _best_reference

def find_nearest_key_in_reference(life, reference, unknown=False, ignore_current=False):
	_lowest = {'chunk_key': None, 'distance': 9000}

	for _key in reference:
		if unknown and _key in life['known_chunks']:
			continue
		
		if ignore_current and lfe.get_current_chunk_id(life) == _key:
			print 'ignoring current'
		
		if not maps.get_chunk(_key)['ground']:
			continue
		
		_center = [int(val)+(SETTINGS['chunk size']/2) for val in _key.split(',')]
		_distance = numbers.distance(life['pos'], _center)
		
		if not _lowest['chunk_key'] or _distance<_lowest['distance']:
			_lowest['distance'] = _distance
			_lowest['chunk_key'] = _key
	
	return _lowest['chunk_key']

def find_nearest_key_in_reference_exact(position, reference):
	_lowest = {'chunk_key': None, 'distance': 100}

	for _key in reference:		
		if not maps.get_chunk(_key)['ground']:
			continue
		
		_center = [int(val)+(SETTINGS['chunk size']/2) for val in _key.split(',')]
		_distance = numbers.distance(position, _center)
		
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

def find_least_controlled_key_in_reference(life, reference):
	_lowest = {'chunk_key': None, 'score': 0}
	
	if not life['camp']:
		logging.warning('Should not be happening!')
		return None
	
	for _key in reference:
		_chunk = maps.get_chunk(_key)
		
		if CAMPS[life['camp']]['name'] in _chunk['control']:
			_score = _chunk['control'][CAMPS[life['camp']]['name']]
			
			if chunks.is_in_chunk(life, _key) and _score == 1:
				_score = -1
		else:
			_score = 0
		
		if not _lowest['chunk_key'] or _score<_lowest['score']:
			_lowest['chunk_key'] = _key
			_lowest['score'] = _score
		
		if _score == -1:
			break
	
	return _lowest['chunk_key']

def path_along_reference(life, ref_type):
	_best_reference = _find_best_unknown_reference(life, ref_type)['reference']

	if not _best_reference:
		print 'NO BEST'
		return False

	_starting_chunk_key = find_nearest_key_in_reference(life, _best_reference)
	_starting_chunk = maps.get_chunk(_starting_chunk_key)
	_chunk_path_keys = []
	_directions = {}
	
	for neighbor_key in _starting_chunk['neighbors']:
		if maps.get_chunk(neighbor_key) == lfe.get_current_chunk(life):
			continue
		
		_neighbor_pos = [int(val)+(SETTINGS['chunk size']/2) for val in neighbor_key.split(',')]
		_cent = (lfe.get_current_chunk(life)['pos'][0]+(SETTINGS['chunk size']/2),
			lfe.get_current_chunk(life)['pos'][1]+(SETTINGS['chunk size']/2))
		_neighbor_direction = numbers.direction_to(_cent, _neighbor_pos)
		_directions[_neighbor_direction] = {'key': neighbor_key, 'score': 9999}
	
	_best_dir = {'dir': -1, 'score': 0}
	for mod in range(-45, 361, 45):
		_new_dir = life['discover_direction']+mod
		
		if _new_dir>=360:
			_new_dir -= 360
		
		if _new_dir in _directions:
			#_score = len(maps.get_chunk(_directions[_new_dir]['key'])['neighbors'])
			_score = 0
			
			if _directions[_new_dir]['key'] in life['known_chunks']:
				continue
			
			_score += (180-(abs(_new_dir-life['discover_direction'])))/45
			_score += life['discover_direction_history'].count(_new_dir)
			
			if _score>=_best_dir['score']:
				if _score==_best_dir['score']:
					_chunk = maps.get_chunk(_directions[_new_dir]['key'])
					#_score += numbers.distance(life['pos'], _chunk['pos'])
				
				_best_dir['dir'] = _new_dir
				_best_dir['score'] = _score
				#print 'b'

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
	for r_type in REFERENCE_MAP:
		for reference in REFERENCE_MAP[r_type]:
			if is_in_reference(position, reference):
				return reference
	
	return False

def life_is_in_reference(life, reference):
	return is_in_reference(life['pos'], reference)

def find_nearest_road(position, skip_unknown=True, ignore_array=[]):
	
	return _find_nearest_reference_exact(position, 'roads')

def find_nearest_building(life, skip_unknown=True, ignore_array=[]):
	return _find_nearest_reference(life, 'buildings', skip_unknown=skip_unknown, ignore_array=ignore_array)
