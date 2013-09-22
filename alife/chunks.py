from globals import *
import life as lfe

import references
import judgement
import logic
import sight
import maps

import logging
import numbers
import random
import time

def get_flag(life, chunk_id, flag):
	if not chunk_id in life['known_chunks']:
		logging.warning('ALife \'%s\' does not know about chunk \'%s\'' % (' '.join(life['name']), chunk_id))
		return False
	
	if flag in life['known_chunks'][chunk_id]['flags']:
		return life['known_chunks'][chunk_id]['flags'][flag]
	
	return False

def flag(life, chunk_id, flag, value):
	#if not flag in life['known_chunks'][chunk_id]['flags']:
	#	logging.debug('%s flagged chunk \'%s\' with %s.' % (' '.join(life['name']), chunk_id, flag))
	
	life['known_chunks'][chunk_id]['flags'][flag] = value

def flag_global(chunk_key, flag, value):
	maps.get_chunk(chunk_key)['flags'][flag] = value

def get_global_flag(chunk_key, flag):
	if flag in maps.get_chunk(chunk_key)['flags']:
		return maps.get_chunk(chunk_key)['flags'][flag]
	
	return False

def get_chunk(chunk_key):
	return maps.get_chunk(chunk_key)

def get_chunk_pos(chunk_id, center=False):
	if center:
		return [int(val)+(map_gen['chunk_size']/2) for val in chunk_id.split(',')]
	
	return [int(val) for val in chunk_id.split(',')]

def get_visible_chunks_from(pos, vision):
	_center_chunk_key = get_chunk_key_at(pos)
	
	_chunk_keys = []
	for chunk_key in sight._scan_surroundings(_center_chunk_key, WORLD_INFO['chunk_size'], vision):
		if not chunk_key in WORLD_INFO['chunk_map']:
			continue
		
		if not can_see_chunk_from_pos(pos, chunk_key, vision=vision):
			continue
		
		_chunk_keys.append(chunk_key)
	
	return _chunk_keys

def get_chunk_key_at(pos):
	return '%s,%s' % ((pos[0]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'], (pos[1]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'])

def find_best_chunk(life, ignore_starting=False, ignore_time=False, lost_method=None, only_unvisted=False, only_unseen=False, only_recent=False):
	_interesting_chunks = {}
	
	for chunk_key in life['known_chunks']:
		_chunk = life['known_chunks'][chunk_key]
		
		if not ignore_time and _chunk['last_visited'] == -1 or time.time()-_chunk['last_visited']>=900:
			if only_unvisted and not _chunk['last_visited'] == -1:
				continue
			
			if only_unseen and not _chunk['last_seen'] == -1:
				continue
			
			_interesting_chunks[chunk_key] = life['known_chunks'][chunk_key]
		elif ignore_time:
			if only_unvisted and not _chunk['last_visited'] == -1:
				continue
			
			if only_unseen and not _chunk['last_seen'] == -1:
				continue
			
			_interesting_chunks[chunk_key] = life['known_chunks'][chunk_key]
	
	if not ignore_starting:
		_current_known_chunk = lfe.get_current_known_chunk(life)
		_initial_score = _current_known_chunk['score']
	else:
		_initial_score = 0
	
	if only_recent:
		_recent = -1
		for chunk_key in _interesting_chunks.keys():
			chunk = _interesting_chunks[chunk_key]
			
			if chunk['discovered_at']>_recent:
				_recent = chunk['discovered_at']
	
	_best_chunk = {'score': _initial_score, 'chunk_key': None}
	for chunk_key in _interesting_chunks:
		chunk = _interesting_chunks[chunk_key]
		_score = chunk['score']

		if only_recent:
			if chunk['discovered_at']<_recent:
				continue
		
		if lost_method == 'furthest':
			chunk_center = [int(val)+(WORLD_INFO['chunk_size']/2) for val in chunk_key.split(',')]
			_score = numbers.distance(life['pos'], chunk_center)
			
			if ignore_starting and chunk_key == lfe.get_current_chunk_id(life):
				continue
		
		if _score>_best_chunk['score']:
			_best_chunk['score'] = _score
			_best_chunk['chunk_key'] = chunk_key
		
	if not _best_chunk['chunk_key']:
		return False
	
	return _best_chunk['chunk_key']

#def find_best_unknown_chunk(life, chunks):
#	_nearest = {'distance': -1, 'key': None}
#	for chunk_key in references.find_nearest_road(life):
#		if chunk_key in life['known_chunks']:
#			continue
#		
#		chunk_center = [int(val)+(WORLD_INFO['chunk_size']/2) for val in chunk_key.split(',')]
#		_distance = numbers.distance(life['pos'], chunk_center)
#		
#		if not _nearest['key'] or _distance<_nearest['distance']:
#			_nearest['distance'] = _distance
#			_nearest['key'] = chunk_key
#	
#	return _nearest['key']

def find_surrounding_unknown_chunks(life):
	_unknown_chunks = []
	
	for chunk_id in lfe.get_surrounding_unknown_chunks(life):
		if can_see_chunk(life, chunk_id):
			_unknown_chunks.append(chunk_id)
	
	return _unknown_chunks

def is_in_chunk(life, chunk_key):
	_chunk = maps.get_chunk(chunk_key)
	
	if life['pos'][0] >= _chunk['pos'][0] and life['pos'][0] <= _chunk['pos'][0]+WORLD_INFO['chunk_size']\
		and life['pos'][1] >= _chunk['pos'][1] and life['pos'][1] <= _chunk['pos'][1]+WORLD_INFO['chunk_size']:
			return True
	
	return False

def position_is_in_chunk(position, chunk_id):
	_chunk = maps.get_chunk(chunk_id)
	
	if position[0] >= _chunk['pos'][0] and position[0] <= _chunk['pos'][0]+WORLD_INFO['chunk_size']\
		and position[1] >= _chunk['pos'][1] and position[1] <= _chunk['pos'][1]+WORLD_INFO['chunk_size']:
			return True
	
	return False

def get_alife_in_chunk_matching(chunk_key, matching):
	_life = []
	_chunk = maps.get_chunk(chunk_key)
	
	for alife in [LIFE[l] for l in _chunk['life']]:
		if logic.matches(alife, matching):
			_life.append(alife['id'])
	
	return _life

def get_nearest_position_in_chunk(position, chunk_id):
	_closest = {'pos': None, 'score': 0}
	
	for pos in get_walkable_areas(chunk_id):
		_dist = numbers.distance(position, pos)
		
		if not _closest['pos'] or _dist<_closest['score']:
			_closest['pos'] = pos
			_closest['score'] = _dist
	
	return _closest['pos']

def _get_nearest_chunk_in_list(pos, chunks):
	_nearest_chunk = {'chunk_key': None, 'distance': -1}
	
	for chunk_key in chunks:
		chunk_center = [int(val)+(WORLD_INFO['chunk_size']/2) for val in chunk_key.split(',')]
		_dist = numbers.distance(pos, chunk_center)
		
		if not _nearest_chunk['chunk_key'] or _dist < _nearest_chunk['distance']:
			_nearest_chunk['distance'] = _dist
			_nearest_chunk['chunk_key'] = chunk_key
	
	return _nearest_chunk

def get_nearest_chunk_in_list(pos, chunks):
	return _get_nearest_chunk_in_list(pos, chunks)['chunk_key']

def get_distance_to_hearest_chunk_in_list(pos, chunks):
	return _get_nearest_chunk_in_list(pos, chunks)['distance']

def _can_see_chunk_quick(start_pos, chunk_id, vision):
	chunk = maps.get_chunk(chunk_id)
	
	if not len(chunk['ground']):
		return False
	
	for pos in [(0, 0), (1, 0), (0, 1), (1, 1)]:
		_x = pos[0]*WORLD_INFO['chunk_size']
		_y = pos[1]*WORLD_INFO['chunk_size']
		
		if _x:
			_x -= 1
		if _y:
			_y -= 1
		
		_can_see = sight._can_see_position(start_pos, (chunk['pos'][0]+_x, chunk['pos'][1]+_y), max_length=vision)
		
		if _can_see:
			return _can_see
	
	return False

def can_see_chunk(life, chunk_key, distance=True):
	return can_see_chunk_from_pos(life['pos'], chunk_key, distance=distance, vision=sight.get_vision(life))
	#_fast_see = _can_see_chunk_quick(life['pos'], chunk_id, sight.get_vision(life))
	#
	#if _fast_see:
	#	return _fast_see
	#
	#chunk = maps.get_chunk(chunk_id)
	#
	#for pos in chunk['ground']:
	#	_can_see = sight.can_see_position(life, pos, distance=distance)
	#	
	#	if _can_see:
	#		return _can_see
	#
	#return False

def can_see_chunk_from_pos(pos1, chunk_key, distance=True, vision=10):
	_fast_see = _can_see_chunk_quick(pos1, chunk_key, vision)
	
	if _fast_see:
		return _fast_see
	
	chunk = maps.get_chunk(chunk_key)
	
	for pos in chunk['ground']:
		_can_see = sight._can_see_position(pos1, pos, distance=distance)
		
		if _can_see:
			return _can_see
	
	return False

def get_walkable_areas(chunk_id):
	return maps.get_chunk(chunk_id)['ground']

def get_visible_walkable_areas(life, chunk_id):
	chunk = maps.get_chunk(chunk_id)
	_walkable = []
	
	for pos in chunk['ground']:
		if sight.can_see_position(life, pos):
			_walkable.append(pos)
	
	return _walkable
