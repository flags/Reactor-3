from globals import WORLD_INFO, MAP_SIZE, SETTINGS
from libc.stdlib cimport malloc, free

import zones as zon

import numbers

import time
import copy

cdef distance(pos1, pos2):
	cdef int x_dist, y_dist
	cdef int *_pos1 = <int *>malloc(2 * 2 * sizeof(int))
	cdef int *_pos2 = <int *>malloc(2 * 2 * sizeof(int))
	
	_pos1[0] = pos1[0]
	_pos1[1] = pos1[1]
	_pos2[0] = pos2[0]
	_pos2[1] = pos2[1]
		
	x_dist = abs(_pos1[0]-_pos2[0])
	y_dist = abs(_pos1[1]-_pos2[1])
	
	free(_pos1)
	free(_pos2)
	
	if x_dist > y_dist:
		return y_dist + (x_dist-y_dist)
	else:
		return x_dist + (y_dist-x_dist)

cdef create_map_array(val, size):
	cdef int x, y
	
	_map = []
	for x in range(size[0]):
		_y = []
		
		for y in range(size[1]):
			_y.append(val)
		
		_map.append(_y)
	
	return _map

#@profile
def dijkstra_map(start_pos, goals, zones, max_chunk_distance=5, rolldown=True, avoid_chunks=[], avoid_positions=[], return_score=False, return_score_in_range=[]):
	#Some notes before we begin:
	#	* You can't get cython-created arrays out of this function
	#	* I haven't found a way to create proper dynamically-sized arrays. I've locked them out at 500x500
	
	_init_time = time.time()
	_avoid_positions = avoid_positions[:]
	avoid_positions = []
	for position in _avoid_positions:
		if not position:
			continue
		
		avoid_positions.append(tuple(position[:2]))
	
	cdef int x, y, _x, _y, _n_x, _n_y, _i, _number_of_goals
	cdef float _score
	cdef float _lowest_score
	cdef int _world_map_size_x = MAP_SIZE[0]
	cdef int _world_map_size_y = MAP_SIZE[1]
	cdef int _dijkstra_map_size_x
	cdef int _dijkstra_map_size_y
	cdef int _chunk_size = WORLD_INFO['chunk_size']
	cdef int *_top_left = <int *>malloc(2 * 2 * sizeof(int))
	cdef int *_bot_right = <int *>malloc(2 * 2 * sizeof(int))
	cdef int *_pos = <int *>malloc(2 * 2 * sizeof(int))
	cdef int *_next_pos = <int *>malloc(2 * 2 * sizeof(int))
	cdef int *_goals_x = <int *>malloc(len(goals) * len(goals) * sizeof(int))
	cdef int *_goals_y = <int *>malloc(len(goals) * len(goals) * sizeof(int))
	
	_number_of_goals = len(goals)
	_chunk_keys = {}
	_top_left[0] = _world_map_size_x
	_top_left[1] = _world_map_size_y
	_bot_right[0] = 0
	_bot_right[1] = 0
	
	TEMP_SIZE = 20
	
	for _i in range(_number_of_goals):
		_goals_x[_i] = goals[_i][0]
		_goals_y[_i] = goals[_i][1]
		
		if goals[_i][0] < _top_left[0]:
			_top_left[0] = numbers.clip(goals[_i][0]-TEMP_SIZE, 0, MAP_SIZE[0])
		
		if goals[_i][0] > _bot_right[0]:
			_bot_right[0] = numbers.clip(goals[_i][0]+TEMP_SIZE, 0, MAP_SIZE[0])
		
		if goals[_i][1] < _top_left[1]:
			_top_left[1] = numbers.clip(goals[_i][1]-TEMP_SIZE, 0, MAP_SIZE[1])
		
		if goals[_i][1] > _bot_right[1]:
			_bot_right[1] = numbers.clip(goals[_i][1]+TEMP_SIZE, 0, MAP_SIZE[1])
	
	if start_pos[0]<_top_left[0]:
		_top_left[0] = numbers.clip(start_pos[0]-TEMP_SIZE, 0, MAP_SIZE[0])
	elif start_pos[0]>_bot_right[0]:
		_bot_right[0] = numbers.clip(start_pos[0]+TEMP_SIZE, 0, MAP_SIZE[0])
	
	if start_pos[1]<_top_left[1]:
		_top_left[1] = numbers.clip(start_pos[1]-TEMP_SIZE, 0, MAP_SIZE[1])
	elif start_pos[1]>_bot_right[1]:
		_bot_right[1] = numbers.clip(start_pos[1]+TEMP_SIZE, 0, MAP_SIZE[1])
	
	if SETTINGS['print dijkstra maps']:
		print 'debug'
		print 'start_pos', start_pos
		print 'top_left', (_top_left[0], _top_left[1])
		print 'bot_right', (_bot_right[0], _bot_right[1])	
		
		for goal in goals:
			print 'goal', goal
	
	_open_map = create_map_array(-3, MAP_SIZE)
	
	_avoid_goals = []
	for zone in [zon.get_slice(z) for z in zones]:
		for y in range(_top_left[1], _bot_right[1]):
			for x in range(_top_left[0], _bot_right[0]):
				#print 'running first', time.time(), (_top_left[1], _bot_right[1]), (_top_left[0], _bot_right[0])
				#print 'looping'
				if (x, y) in avoid_positions:
					continue
				
				if _open_map[x][y]>-3:
					continue
				
				if not zone['_map'][x-zone['top_left'][0]-1][y-zone['top_left'][1]-1]:
					continue
				
				_chunk_key = '%s,%s' % ((x/_chunk_size)*_chunk_size, (y/_chunk_size)*_chunk_size)
				
				if avoid_chunks and _chunk_key in avoid_chunks:
					_avoid_goals.append((x, y))
					#continue
					
				_open_map[x][y] = 1
				
				_chunk = WORLD_INFO['chunk_map'][_chunk_key]
				
				_pass = False
				for i in range(0, _number_of_goals):
					_goal_chunk_key = '%s,%s' % ((_goals_x[i]/_chunk_size)*_chunk_size, (_goals_y[i]/_chunk_size)*_chunk_size)
					_goal_chunk = WORLD_INFO['chunk_map'][_goal_chunk_key]
					
					if distance(_chunk['pos'], _goal_chunk['pos'])/_chunk_size<=max_chunk_distance:
						_pass = True
						break
				
				if not _pass:
					continue
				
				#if x<_top_left[0]:
				#	_top_left[0] = x
					
				#if y<_top_left[1]:
				#	_top_left[1] = y
				
				#if x>_bot_right[0]:
				#	_bot_right[0] = x
				
				#if y>_bot_right[1]:
				#	_bot_right[1] = y
				
				_chunk_keys[_chunk_key] = zone['id']
	
	_dijkstra_map_size_x = _bot_right[0]-_top_left[0]
	_dijkstra_map_size_y = _bot_right[1]-_top_left[1]
	#cdef float _dijkstra_map[500][500]
	cdef float *_dijkstra_map = <float *>malloc(500 * 500 * sizeof(float))
	cdef float *_old_map = <float *>malloc(500 * 500 * sizeof(float))
	
	for y in range(0, _dijkstra_map_size_y):
		for x in range(0, _dijkstra_map_size_x):
			_x = x+_top_left[0]
			_y = y+_top_left[1]
	
			if _open_map[_x][_y]<=0:
				_dijkstra_map[x + y * 500] = -99999
				_old_map[x + y * 500] = -99999
			else:
				_dijkstra_map[x + y * 500] = 99999
				_old_map[x + y * 500] = 99999
	
	goals.extend(_avoid_goals)
	for goal in goals:
		_x = goal[0]-_top_left[0]
		_y = goal[1]-_top_left[1]
		
		_dijkstra_map[_x + _y * 500] = 0
	
	_changed = True
	
	_change_time = time.time()
	while _changed:
		_changed = False
		
		for y in range(0, _dijkstra_map_size_y):
			for x in range(0, _dijkstra_map_size_x):
				if _old_map[x + y * 500]<=0:
					continue
				
				_old_map[x + y * 500] = _dijkstra_map[x + y * 500]
				
				_lowest_score = _old_map[x + y * 500]
				
				for _n_x,_n_y in [(0, -1), (-1, 0), (1, 0), (0, 1)]:#, (-1, -1), (1, -1), (-1, 1), (1, 1)]:
				#for _n_y in range(-1, 2):
					#_y = y+_n_y
					_y = y+_n_y
					
					if _y<0 or _y>=_dijkstra_map_size_y:
						continue
					
					#for _n_x in range(-1, 2):
					#_x = x+_n_x
					_x = x+_n_x
					
					if _x<0 or _x>=_dijkstra_map_size_x:
						continue
					
					if _old_map[_x + _y * 500]<0:
						continue
					
					_score = _old_map[_x + _y * 500]
					
					if _score<_lowest_score:
						_lowest_score = _score
					
				if _old_map[x + y * 500]-_lowest_score>=2:
					_dijkstra_map[x + y * 500] = _lowest_score+1
					_changed=True
	
	if not rolldown:
		for y in range(0, _dijkstra_map_size_y):
			for x in range(0, _dijkstra_map_size_x):
				if _dijkstra_map[x + y * 500]<=0:
					continue
				
				_dijkstra_map[x + y * 500] *= -1.2
				_old_map[x + y * 500] *= -1.2	
	
	if SETTINGS['print dijkstra maps']:
		for y in range(0, _bot_right[1]-_top_left[1]):#_map_info['size'][1]):
			for x in range(0, _bot_right[0]-_top_left[0]):
				if [x+_top_left[0], y+_top_left[1]] == start_pos[:2]:
					print 'X',
				elif rolldown:
					if _dijkstra_map[x + y * 500]>0:
						print int(numbers.clip(_dijkstra_map[x + y * 500], 0, 9)),
					else:
						print '#',
				else:
					if _dijkstra_map[x + y * 500]<0:
						print int(numbers.clip(-_dijkstra_map[x + y * 500], 0, 9)),
					else:
						print '#',
			
			print	
	
	if return_score:
		_score = _dijkstra_map[(start_pos[0]-_top_left[0]) + (start_pos[1]-_top_left[1]) * 500]
		free(_old_map)
		free(_dijkstra_map)
		return _score
	
	if return_score_in_range:
		#for y in range(0, _bot_right[1]-_top_left[1]):#_map_info['size'][1]):
		#	for x in range(0, _bot_right[0]-_top_left[0]):
		#		if rolldown:
		#			if _dijkstra_map[x + y * 500]>0:
		#				print int(round(numbers.clip(_dijkstra_map[x + y * 500], 0, 9))),
		#			else:
		#				print '#',
		#		else:
		#			if _dijkstra_map[x + y * 500]<0:
		#				print int(round(numbers.clip(-_dijkstra_map[x + y * 500], 0, 9))),
		#			else:
		#				print '#',
		#	
		#	print
		_positions = []
		for y in range(0, _bot_right[1]-_top_left[1]):
			for x in range(0, _bot_right[0]-_top_left[0]):
				if _dijkstra_map[x + y * 500] in range(return_score_in_range[0], return_score_in_range[1]):
					_positions.append((_top_left[0]+x, _top_left[1]+y))
		
		free(_old_map)
		free(_dijkstra_map)
		
		return _positions
	
	#for y in range(0, _bot_right[1]-_top_left[1]):#_map_info['size'][1]):
	#	for x in range(0, _bot_right[0]-_top_left[0]):
	#		if rolldown:
	#			if _dijkstra_map[x + y * 500]>0:
	#				print int(round(numbers.clip(_dijkstra_map[x + y * 500], 0, 9))),
	#			else:
	#				print '#',
	#		else:
	#			if _dijkstra_map[x + y * 500]<0:
	#				print int(round(numbers.clip(-_dijkstra_map[x + y * 500], 0, 9))),
	#			else:
	#				print '#',
	#	
	#	print
	
	_path = []
	_pos[0] = start_pos[0]-_top_left[0]
	_pos[1] = start_pos[1]-_top_left[1]
	
	while 1:
		if rolldown and _dijkstra_map[_pos[0] + _pos[1] * 500]<=0:
			break
		elif not rolldown and _dijkstra_map[_pos[0] + _pos[1] * 500]>0:
			break
		
		_lowest_score = _old_map[_pos[0] + _pos[1] * 500]
		_next_pos[0] = -1
		_next_pos[1] = -1
				
		#for pos in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
		for _n_y in range(-1, 2):
			_y = _pos[1]+_n_y
			
			if _y<0 or _y>=_dijkstra_map_size_y:
				continue
			
			for _n_x in range(-1, 2):
				if _n_x == 0 and _n_y == 0:
					continue
				
				_x = _pos[0]+_n_x
				
				if _x<0 or _x>=_dijkstra_map_size_x:
					continue
				
				if rolldown:
					if _dijkstra_map[_x + _y * 500]<0:
						continue
				else:
					if _dijkstra_map[_x + _y * 500]>=0 or _open_map[_x+_top_left[0]][_y+_top_left[1]]==-3:
						continue
				
				_score = _dijkstra_map[_x + _y * 500]
				
				if _score<_lowest_score:
					_lowest_score = _score
					_next_pos[0] = _x
					_next_pos[1] = _y
		
		if _lowest_score == _old_map[_pos[0] + _pos[1] * 500]:
			break
		else:
			_path.append((_next_pos[0]+_top_left[0], _next_pos[1]+_top_left[1], 2))
		
		if (_next_pos[0], _next_pos[1]) == (_pos[0], _pos[1]):
			break
		
		_pos[0] = _next_pos[0]
		_pos[1] = _next_pos[1]

	free(_old_map)
	free(_dijkstra_map)

	return _path