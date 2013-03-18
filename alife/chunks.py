from globals import *
import life as lfe

import references
import maps

import numbers
import random
import time

def find_best_known_chunk(life):
	_interesting_chunks = {}
	
	for chunk_key in life['known_chunks']:
		_chunk = life['known_chunks'][chunk_key]
		
		if _chunk['last_visited'] == 0 or time.time()-_chunk['last_visited']>=900:
			_interesting_chunks[chunk_key] = life['known_chunks'][chunk_key]
	
	_current_known_chunk = lfe.get_current_known_chunk(life)
	if _current_known_chunk:
		_initial_score = _current_known_chunk['score']
	else:
		_initial_score = 0
	
	_best_chunk = {'score': _initial_score, 'chunk_key': None}
	for chunk_key in _interesting_chunks:
		chunk = _interesting_chunks[chunk_key]
		
		if chunk['score']>_best_chunk['score']:
			_best_chunk['score'] = chunk['score']
			_best_chunk['chunk_key'] = chunk_key
		
	if not _best_chunk['chunk_key']:
		return False
	
	return _best_chunk['chunk_key']

def find_best_unknown_chunk(life, chunks):
	_nearest = {'distance': -1, 'key': None}
	for chunk_key in references.find_nearest_road(life):
		if chunk_key in life['known_chunks']:
			continue
		
		chunk_center = [int(val)+(SETTINGS['chunk size']/2) for val in chunk_key.split(',')]
		_distance = numbers.distance(life['pos'], chunk_center)
		
		if not _nearest['key'] or _distance<_nearest['distance']:
			_nearest['distance'] = _distance
			_nearest['key'] = chunk_key
	
	return _nearest['key']

def find_surrounding_unknown_chunks(life):
	_unknown_chunks = []
	
	for chunk_id in lfe.get_surrounding_unknown_chunks(life):
		if can_see_chunk(life, chunk_id):
			_unknown_chunks.append(chunk_id)
	
	return _unknown_chunks

def is_in_chunk(life, chunk_id):
	_chunk = maps.get_chunk(chunk_id)
	
	if life['pos'][0] >= _chunk['pos'][0] and life['pos'][0] <= _chunk['pos'][0]+SETTINGS['chunk size']\
		and life['pos'][1] >= _chunk['pos'][1] and life['pos'][1] <= _chunk['pos'][1]+SETTINGS['chunk size']:
			return True
	
	return False

def can_see_chunk(life, chunk_id):
	chunk = maps.get_chunk(chunk_id)
	
	for pos in chunk['ground']:
		if lfe.can_see(life, pos):
			return True
	
	return False

def get_walkable_areas(life, chunk_id):
	return maps.get_chunk(chunk_id)['ground']

def get_visible_walkable_areas(life, chunk_id):
	chunk = maps.get_chunk(chunk_id)
	_walkable = []
	
	for pos in chunk['ground']:
		if lfe.can_see(life, pos):
			_walkable.append(pos)
	
	return _walkable
