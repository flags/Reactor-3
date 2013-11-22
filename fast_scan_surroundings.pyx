from globals import WORLD_INFO
from libc.stdlib cimport malloc, free

import fast_dijkstra
import life as lfe

import drawing
import numbers
import alife
import maps

def scan_surroundings(life, initial=False, _chunks=[], ignore_chunks=[], judge=True, get_chunks=False, visible_check=True):
	cdef char *chunk_key = <char*>malloc((9+1))
	cdef int i, _chunk_x, _chunk_y, _dist
	cdef CHUNK_SIZE = WORLD_INFO['chunk_size']
	
	_center_chunk_key = lfe.get_current_chunk_id(life)
	
	if get_chunks:
		_center_chunk = maps.get_chunk(_center_chunk_key)
	
	_visible_chunks = set()
	
	if _chunks:
		_chunks = [c for c in _chunks if c in WORLD_INFO['chunk_map']]
	else:
		_temp_chunks = alife.sight._scan_surroundings(_center_chunk_key, CHUNK_SIZE, alife.sight.get_vision(life), ignore_chunks=ignore_chunks)
		_chunks = []
		for _chunk in _temp_chunks:
			if _chunk in WORLD_INFO['chunk_map']:
				_chunks.append(_chunk)
	
	#Find chunks furthest away
	if visible_check:
		_outline_chunks = {'distance': 0, 'chunks': []}
		
		for i in range(len(_chunks)):
			chunk_key = _chunks[i]
			
			_current_chunk = maps.get_chunk(chunk_key)
			_dist = numbers.distance(life['pos'], (_current_chunk['pos'][0]+CHUNK_SIZE/2, _current_chunk['pos'][1]+CHUNK_SIZE/2))
			
			if _dist>_outline_chunks['distance']+CHUNK_SIZE:
				_outline_chunks['distance'] = _dist
				_outline_chunks['chunks'] = [chunk_key]
			elif _dist>=_outline_chunks['distance']:
				_outline_chunks['chunks'].append(chunk_key)
		
		for outline_chunk_key in _outline_chunks['chunks']:
			if outline_chunk_key in _visible_chunks:
				continue
			
			_outline_chunk = WORLD_INFO['chunk_map'][outline_chunk_key]
			if _outline_chunk['max_z'] <= life['pos'][2]:
				_can_see = drawing.diag_line(life['pos'], (_outline_chunk['pos'][0]+CHUNK_SIZE/2, _outline_chunk['pos'][1]+CHUNK_SIZE/2))
			else:
				_can_see = alife.chunks.can_see_chunk(life, outline_chunk_key)
			
			if _can_see:
				_skip = 0
				for pos in _can_see:
					#if _skip:
					#	_skip-=1
					#	continue
					
					#if _can_see.index(pos)<len(_can_see)-6 and not _skip:
					#	_skip = 5
					
					_chunk_key = alife.chunks.get_chunk_key_at(pos)
					if not _chunk_key in _visible_chunks:
						if judge:
							if initial:
								alife.judgement.judge_chunk(life, _chunk_key, seen=True)
							else:
								alife.judgement.judge_chunk(life, _chunk_key)
						
						_visible_chunks.add(_chunk_key)
						
						if _chunk_key in _chunks:
							_chunks.remove(_chunk_key)
			else:
				_chunks.remove(outline_chunk_key)
	
	for i in range(len(_chunks)):
		chunk_key = _chunks[i]
		
		if not chunk_key in WORLD_INFO['chunk_map']:
			continue
		
		if visible_check and not WORLD_INFO['chunk_map'][chunk_key]['max_z']<=life['pos'][2]:
			if not alife.chunks.can_see_chunk(life, chunk_key):
				continue
		
		if get_chunks:
			_visible_chunks.add(chunk_key)
		
		if judge:
			if initial:
				alife.judgement.judge_chunk(life, chunk_key, seen=True)
			else:
				alife.judgement.judge_chunk(life, chunk_key)
	
	if get_chunks:
		return list(_visible_chunks)
