from globals import *
from math import *
import pathfinding
import render_los
import logging
import random
import numpy
import tiles
import time
import maps

def clip(number,start,end):
	"""Returns `number`, but makes sure it's in the range of [start..end]"""
	return max(start, min(number, end))

def roll(dice, sides):
	return sum([random.choice(list(range(sides)))+1 for d in range(dice)])

def lerp(n1, n2, t):
	return n1 + (n2-n1) * t

def distance(pos1, pos2, old=False):
	if old:
		return abs(pos1[0]-pos2[0])+abs(pos1[1]-pos2[1])
		
	x_dist = abs(pos1[0]-pos2[0])
	y_dist = abs(pos1[1]-pos2[1])
	
	if x_dist > y_dist:
		return y_dist + (x_dist-y_dist)
	else:
		return x_dist + (y_dist-x_dist)

def velocity(direction, speed):
	rad = direction*(pi/180)
	velocity = numpy.multiply(numpy.array([cos(rad), sin(rad)]), speed)
	
	return [velocity[0], -velocity[1], 0]

def lerp_velocity(velocity1, velocity2, interp):
	return [lerp(velocity1[0], velocity2[0], interp),
	        lerp(velocity1[1], velocity2[1], interp),
	        lerp(velocity1[2], velocity2[2], interp)]

def get_surface_area(structure):
	if 'attaches_to' in structure:
		return structure['size']*len(structure['attaches_to'])
	
	return structure['size']

def direction_to(pos1, pos2):
	theta = atan2((pos1[1]-pos2[1]), -(pos1[0]-pos2[0]))
		
	if theta < 0:
		theta += 2 * pi
	
	return theta * (180/pi)

def create_flee_map(dijkstra):
	for _x in range(dijkstra['x_range'][0],dijkstra['x_range'][1]):
		for _y in range(dijkstra['y_range'][0],dijkstra['y_range'][1]):
			if dijkstra['map'][_y-dijkstra['y_range'][0],_x-dijkstra['x_range'][0]]==9999:
				continue
			
			dijkstra['map'][_y-dijkstra['y_range'][0],_x-dijkstra['x_range'][0]] *= -1.25

def calculate_dijkstra_map(dijkstra):
	_map = dijkstra['map']
	_min_x = dijkstra['x_range'][0]
	_max_x = dijkstra['x_range'][1]
	_min_y = dijkstra['y_range'][0]
	_max_y = dijkstra['y_range'][1]
	_target_positions = [tuple(target['position']) for target in dijkstra['targets']]
	
	_i = 0
	while 1==1:
		_i += 1
		_orig_map = _map.copy()
		
		for _x in range(_min_x,_max_x):
			for _y in range(_min_y,_max_y):
				if (_x,_y) in _target_positions or _orig_map[_y-_min_y,_x-_min_x] == -1:
					
					continue
				
				_lowest_score = 9000
				
				for x1 in range(-1,2):
					x = _x+x1
					
					if 0>x or x>=_max_x:
						continue
					
					for y1 in range(-1,2):
						#if (x1,y1) in [(-1,-1),(1,-1),(-1,1),(1,1)]:
						#	continue
						
						y = _y+y1
						
						if 0>y or y>=_max_y or (x1,y1) == (0,0) or _orig_map[y-_min_y,x-_min_x] == -1:
							continue
						
						if _orig_map[y-_min_y,x-_min_x] < _lowest_score:
							_lowest_score = _orig_map[y-_min_y,x-_min_x]
				
				if _lowest_score>=0:
					if _orig_map[_y-_min_y,_x-_min_x]-_lowest_score>=2:
						_map[_y-_min_y,_x-_min_x] = _lowest_score+1
		
		if numpy.array_equal(_map,_orig_map):
			break

def _create_dijkstra_map(center,source_map,targets,size=(50,50),flee=False,**kvargs):
	if not targets:
		raise Exception('No targets passed to create_dijkstra_map()')
	
	_target_positions = [tuple(target['position']) for target in targets]
	
	_min_x = clip(center[0]-(size[0]),0,MAP_SIZE[0])
	_max_x = clip(center[0]+(size[0]),0,MAP_SIZE[0])
	
	_min_y = clip(center[1]-(size[1]),0,MAP_SIZE[1])
	_max_y = clip(center[1]+(size[1]),0,MAP_SIZE[1])
	
	_stime = time.time()
	
	_map = numpy.ones((_max_y,_max_x))
	_orig_map = None
	
	for target in targets:
		_map[target['position'][1]-_min_y,target['position'][0]-_min_x] = 0#target['score']
	
	_map*=30
	
	for x in range(_min_x,_max_x):
		for y in range(_min_y,_max_y):			
			if source_map[x][y][center[2]+1]:
				if flee:
					_map[y-_min_y,x-_min_x] = 1
				else:
					_map[y-_min_y,x-_min_x] = -1
				
				continue
	
	_dijkstra = {'map': _map,
		'x_range': (_min_x,_max_x),
		'y_range': (_min_y,_max_y),
		'targets': targets}
	
	calculate_dijkstra_map(_dijkstra)
	
	if flee:
		create_flee_map(_dijkstra)
		#_create_dijkstra_map(center,source_map,targets,size=size)
		calculate_dijkstra_map(_dijkstra)
	
	logging.info('Dijkstra map took: %s, size %s,%s' % (str(time.time()-_stime),(_max_x-_min_x),(_max_y-_min_y)))
	print('Dijkstra map took: %s, size %s,%s, %s' % (str(time.time()-_stime),(_max_x-_min_x),(_max_y-_min_y),0))
	
	return _dijkstra

def draw_dijkstra(dijkstra,path):
	for _y in range(dijkstra['y_range'][0],dijkstra['y_range'][1]):
		y = _y-dijkstra['y_range'][0]
		
		for _x in range(dijkstra['x_range'][0],dijkstra['x_range'][1]):
			x = _x-dijkstra['x_range'][0]
			
			#if _x == 20:
			#	continue
			
			#print _x,dijkstra['x_range']#,_y#,dijkstra['x_range'][1],dijkstra['y_range'][1]
			_score = clip(int(abs(dijkstra['map'][y,x])),0,9)
			#_score = int(dijkstra['map'][y,x])
			
			if (_x,_y,0) in path:
				_score = 'O '
			elif _score == -1:
				_score = 'x '
			else:
				_score = '. '
				#_score = _score
			
			print('%s' % _score, end=' ')
		
		print()

def create_dijkstra_map(center,source_map,targets,flee=False):
	_farthest_distance = 0
	
	for target in targets:
		_dist = distance(center,target['position'])
	
		if _dist>_farthest_distance:
			_farthest_distance = _dist+1
	
	return _create_dijkstra_map(center,source_map,targets,size=(_farthest_distance,_farthest_distance),flee=flee)

