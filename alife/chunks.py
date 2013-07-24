from globals import *
import life as lfe

import references
import judgement
import sight
import maps

import logging
import numbers
import random
import time

def get_flag(life, chunk_id, flag):
	if flag in life['known_chunks'][chunk_id]['flags']:
		return life['known_chunks'][chunk_id]['flags'][flag]
	
	return False

def flag(life, chunk_id, flag, value):
	life['known_chunks'][chunk_id]['flags'][flag] = value
	
	logging.debug('%s flagged chunk \'%s\' with %s.' % (' '.join(life['name']), chunk_id, flag))

def find_best_chunk(life, ignore_starting=False, ignore_time=False, all_visible=False, lost_method=None):
	_interesting_chunks = {}
	
	if all_visible:
		_center_chunk = lfe.get_current_chunk_id(life)
		for x_mod in [-1, 0, 1]:
			for y_mod in [-1, 0, 1]:
				if not x_mod and not y_mod:
					continue
				
				_pos_mod = [x_mod*WORLD_INFO['chunk_size'], y_mod*WORLD_INFO['chunk_size']]
				_chunk_key = ','.join([str(int(val)+_pos_mod.pop()) for val in _center_chunk.split(',')])
				
				if not _chunk_key in CHUNK_MAP:
					print 'invalid chunk:',_chunk_key
					continue				
				
				if not get_visible_walkable_areas(life, _chunk_key):
					continue
				
				if not _chunk_key in life['known_chunks']:
					judgement.judge_chunk(life, _chunk_key)
				
				_interesting_chunks[_chunk_key] = life['known_chunks'][_chunk_key]
				print life['name'],'VALID'
				
	else:
		for chunk_key in life['known_chunks']:
			_chunk = life['known_chunks'][chunk_key]
			
			if not ignore_time and _chunk['last_visited'] == 0 or time.time()-_chunk['last_visited']>=900:
				_interesting_chunks[chunk_key] = life['known_chunks'][chunk_key]
			elif ignore_time:
				_interesting_chunks[chunk_key] = life['known_chunks'][chunk_key]
	
	if not ignore_starting:
		_current_known_chunk = lfe.get_current_known_chunk(life)
		_initial_score = _current_known_chunk['score']
	else:
		_initial_score = 0
	
	_best_chunk = {'score': _initial_score, 'chunk_key': None}
	for chunk_key in _interesting_chunks:
		chunk = _interesting_chunks[chunk_key]
		_score = chunk['score']
		
		if lost_method == 'furthest':
			chunk_center = [int(val)+(WORLD_INFO['chunk_size']/2) for val in chunk_key.split(',')]
			_score = numbers.distance(life['pos'], chunk_center)
			print life['name'],_score,_best_chunk['score']
		
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

def is_in_chunk(life, chunk_id):
	_chunk = maps.get_chunk(chunk_id)
	
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

def get_nearest_position_in_chunk(position, chunk_id):
	_closest = {'pos': None, 'score': 0}
	
	for pos in get_walkable_areas(chunk_id):
		_dist = numbers.distance(position, pos)
		
		if not _closest['pos'] or _dist<_closest['score']:
			_closest['pos'] = pos
			_closest['score'] = _dist
	
	return _closest['pos']

def can_see_chunk(life, chunk_id):
	chunk = maps.get_chunk(chunk_id)
	
	for pos in chunk['ground']:
		if sight.can_see_position(life, pos):
			return True
	
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
