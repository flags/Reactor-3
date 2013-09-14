from globals import WORLD_INFO, MAP_SIZE
from libc.stdlib cimport malloc

import zones as zon

import numbers

import numpy
import copy

def create_map_array(val=0, size=MAP_SIZE):
	cdef int x, y
	
	_map = []
	for x in range(size[0]):
		_y = []
		
		for y in range(size[1]):
			_y.append(val)
		
		_map.append(_y)
	
	return _map

#@profile
def dijkstra_map(start_pos, goals, zones, max_chunk_distance=5, rolldown=True):
	cdef int x, y, _x, _y, _n_x, _n_y
	cdef double _score
	cdef double _lowest_score
	cdef int _world_map_size_x = MAP_SIZE[0]
	cdef int _world_map_size_y = MAP_SIZE[1]
	cdef int _dijkstra_map_size_x
	cdef int _dijkstra_map_size_y
	cdef int _chunk_size = WORLD_INFO['chunk_size']
	cdef int *_top_left = <int *>malloc(2 * 2 * sizeof(int))
	cdef int *_bot_right = <int *>malloc(2 * 2 * sizeof(int))
	
	_open_map = create_map_array(val=-3)
	_chunk_keys = {}
	_top_left[0] = _world_map_size_x
	_top_left[1] = _world_map_size_y
	_bot_right[0] = 0
	_bot_right[1] = 0
	
	#0: Banned
	#1: Open
	
	for zone in [zon.get_slice(z) for z in zones]:
		for y in range(0, _world_map_size_y-1):
			for x in range(0, _world_map_size_x-1):
				if _open_map[x][y]>-3:
					continue
				
				if not zone['map'][x][y] == zone['id'] or zone['map'][x][y] in [-2, -1]:
					continue
				
				_open_map[x][y] = 1
				
				_chunk_key = '%s,%s' % ((x/_chunk_size)*_chunk_size, (y/_chunk_size)*_chunk_size)
				_chunk = WORLD_INFO['chunk_map'][_chunk_key]
				
				_pass = False
				for goal in goals:
					_goal_chunk_key = '%s,%s' % ((goal[0]/_chunk_size)*_chunk_size, (goal[1]/_chunk_size)*_chunk_size)
					_goal_chunk = WORLD_INFO['chunk_map'][_goal_chunk_key]
					
					if numbers.distance(_chunk['pos'], _goal_chunk['pos'])/_chunk_size<=max_chunk_distance:
						_pass = True
						break
				
				if not _pass:
					continue
				
				#Return open map...
				if x<_top_left[0]:
					_top_left[0] = x
					
				if y<_top_left[1]:
					_top_left[1] = y
				
				if x>_bot_right[0]:
					_bot_right[0] = x
				
				if y>_bot_right[1]:
					_bot_right[1] = y
				
				_chunk_keys[_chunk_key] = zone['id']
	
	_map_info = {'open_map': _open_map,
	             'size': (_bot_right[0]-_top_left[0], _bot_right[1]-_top_left[1])}
	#_map_info['map'] = 
	#cdef int *_dijkstra_map = <int *>malloc(_map_info['size'][0] * _map_info['size'][1] * sizeof(int))
	#create_map_array(size=_map_info['size'])
	_dijkstra_map_size_x = _map_info['size'][0]
	_dijkstra_map_size_y = _map_info['size'][1]
	cdef double _dijkstra_map[500][500]
	cdef double _old_map[500][500]
	
	for y in range(0, _dijkstra_map_size_y):
		for x in range(0, _dijkstra_map_size_x):
			_x = x+_top_left[0]
			_y = y+_top_left[1]
	
			if _map_info['open_map'][_x][_y]<=0:
				_dijkstra_map[x][y] = -99999
				_old_map[x][y] = -99999
			else:
				_dijkstra_map[x][y] = 99999
				_old_map[x][y] = 99999
	
	for goal in goals:
		_x = goal[0]-_top_left[0]
		_y = goal[1]-_top_left[1]
		
		_dijkstra_map[_x][_y] = 0
	
	_changed = True
	
	while _changed:
		_changed = False
		#_old_map = copy.deepcopy(_map_info['map'])
		#memcpy(_old_map, _dijkstra_map, sizeof(_dijkstra_map)) ;
		
		for y in range(0, _dijkstra_map_size_y):
			for x in range(0, _dijkstra_map_size_x):
			
				if _old_map[x][y]<=0:
					continue
				
				_old_map[x][y] = _dijkstra_map[x][y]
				
				_lowest_score = _old_map[x][y]
				
				#for pos in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
				for _n_y in range(-1, 2):
					_y = y+_n_y
					
					if _y<0 or _y>=_dijkstra_map_size_y:
						continue
					
					for _n_x in range(-1, 2):
						_x = x+_n_x
						
						if _x<0 or _x>=_dijkstra_map_size_x:
							continue
						
						if _old_map[_x][_y]<0:
							continue
						
						_score = _old_map[_x][_y]
						
						if _score<_lowest_score:
							_lowest_score = _score
					
				if _old_map[x][y]-_lowest_score>=2:
					_dijkstra_map[x][y] = _lowest_score+1
					_changed=True
	
	if not rolldown:
		for y in range(0, _dijkstra_map_size_y):
			for x in range(0, _dijkstra_map_size_x):
				if _dijkstra_map[x][y]<=0:
					continue
				
				_dijkstra_map[x][y] *= -1.2
	
	_path = []
	_pos = [start_pos[0]-_top_left[0], start_pos[1]-_top_left[1]]
	while 1:
		if rolldown and _dijkstra_map[_pos[0]][_pos[1]]<=0:
			print 'WOW break'
			break
		elif not rolldown and _dijkstra_map[_pos[0]][_pos[1]]>=0:
			break
		
		_lowest_score = _old_map[x][y]
		_next_pos = None
				
		#for pos in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
		for _n_y in range(-1, 2):
			for _n_x in range(-1, 2):
				_x = _pos[0]+_n_x
				_y = _pos[1]+_n_y
				
				if _x<0 or _x>=_dijkstra_map_size_x or _y<0 or _y>=_dijkstra_map_size_y:
					continue
				
				if _dijkstra_map[_x][_y]<0:
					continue
				
				_score = _dijkstra_map[_x][_y]
				
				if _score<_lowest_score:
					_lowest_score = _score
					_next_pos = (_x, _y)
		
		if _next_pos:
			_path.append((_next_pos[0]+_top_left[0], _next_pos[1]+_top_left[1], 2))
		else:
			break
		
		if _next_pos == tuple(_pos):
			break
		
		_pos = list(_next_pos)
	
	print _path
	
	for y in range(0, _map_info['size'][1]):
		for x in range(0, _map_info['size'][0]):
			if _dijkstra_map[x][y]>0:
				print numbers.clip(_dijkstra_map[x][y], 0, 9),
			else:
			#	#elif _map_info['map'][x][y] == -3:
				print '#',
				#else:
	#			#print _map_info['map'][x][y],#'#',
	#	
		print

	return _path