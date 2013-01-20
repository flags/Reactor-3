#Accept walls and understand unpassable terrain
#Easily recalcuate map

from numbers import *
import pathfinding
import numbers
import numpy
import maps
import cProfile
import generate_dijkstra_map as fast_gen

def create_dijkstra_map(center,source_map,targets):
	#Calculate the maximum size of the of the map by testing distances to all targets
	_farthest_distance = 10#numbers.distance(center,targets[0]['position'])
	
	print _farthest_distance
	
	_min_x = clip(center[0]-(_farthest_distance),0,MAP_SIZE[0])
	_max_x = clip(center[0]+(_farthest_distance),0,MAP_SIZE[0])
	_min_y = clip(center[1]-(_farthest_distance),0,MAP_SIZE[1])
	_max_y = clip(center[1]+(_farthest_distance),0,MAP_SIZE[1])
	_map = numpy.ones((_max_y,_max_x))
	_ignore = []
	
	#TODO: This number controls how much detail we get in the map
	_map*=30
	
	for x in range(_min_x,_max_x):
		for y in range(_min_y,_max_y):			
			if source_map[x][y][center[2]+1]:
				_ignore.append((x,y))
	
	#Create structure
	_dijkstra = {'map': _map,
		'x_range': (_min_x,_max_x),
		'y_range': (_min_y,_max_y),
		'ignore': _ignore,
		'targets': targets}
	
	return _dijkstra

def generate_dijkstra_map(dijkstra):
	targets = dijkstra['targets']
	_min_x,_max_x = dijkstra['x_range']
	_min_y,_max_y = dijkstra['y_range']
	
	if not targets:
		raise Exception('No targets passed to create_dijkstra_map()')
	
	_target_positions = [tuple(target['position']) for target in targets]
	_map = dijkstra['map']
	_orig_map = None
	
	for target in targets:
		_map[target['position'][1]-_min_y,target['position'][0]-_min_x] = 0
	
	if 'inverted' in dijkstra:
		_starting_lowest = -9000
	else:
		_starting_lowest = 9000
	
	while 1:
		#print 'running'
		_orig_map = _map.copy()
		
		for _x in range(_min_x,_max_x):
			for _y in range(_min_y,_max_y):				
				if (_x,_y) in _target_positions or (_x,_y) in dijkstra['ignore']:
					continue
				
				_real_x = _x-_min_x
				_real_y = _y-_min_y
				
				_lowest_score = _starting_lowest
				
				for x_mod in range(-1,2):
					_map_x_pos = (_real_x)+x_mod
					_xx = _x+x_mod
					
					if 0>_map_x_pos or _map_x_pos>=_map.shape[1]-1:
						continue
					
					for y_mod in range(-1,2):
						_yy = _y+y_mod
						if (x_mod,y_mod) == (0,0) or (_xx,_yy) in dijkstra['ignore']:
							continue
						
						if (x_mod,y_mod) in [(-1,-1),(1,-1),(-1,1),(-1,1)]:
							continue
						
						_dist = 1#numbers.distance((_x,_y),(_xx,_yy))
						
						_map_y_pos = (_real_y)+y_mod
						
						if 0>_map_y_pos or _map_y_pos>=_map.shape[0]-2:	
							continue
						
						if _starting_lowest == 9000:
							#print _orig_map[_y-_min_y,_x-_min_x]-_orig_map[_map_y_pos,_map_x_pos]
							if _orig_map[_real_y,_real_x]-_orig_map[_map_y_pos,_map_x_pos]>=2:
								_lowest_score = _orig_map[_map_y_pos,_map_x_pos]+(1*_dist)
						else:
							#print _orig_map[_y-_min_y,_x-_min_x],_orig_map[_map_y_pos,_map_x_pos]
							if _orig_map[_real_y,_real_x]+_orig_map[_map_y_pos,_map_x_pos]<-2:
								_lowest_score = _orig_map[_map_y_pos,_map_x_pos]+(1)#*_dist)
				
				if _starting_lowest == 9000:
					if _lowest_score < 9000:
						_map[_real_y,_real_x] = _lowest_score
				else:
					if _lowest_score > -9000:
						_map[_real_y,_real_x] = -_lowest_score
				
		if numpy.array_equal(_map,_orig_map):
			break

def invert_dijkstra_map(dijkstra):
	_min_x,_max_x = dijkstra['x_range']
	_min_y,_max_y = dijkstra['y_range']
	
	#for _x in range(_min_x,_max_x):
	#	for _y in range(_min_y,_max_y):	
	#		if(_x,_y) in dijkstra['ignore']:
	#			continue
			
	dijkstra['map'] *= -1.41
	
	#draw_dijkstra(dijkstra)
	
	dijkstra['inverted'] = True
	
	generate_dijkstra_map(dijkstra)

def draw_dijkstra(dijkstra,path=None):
	for _y in range(dijkstra['y_range'][0],dijkstra['y_range'][1]):
		y = _y-dijkstra['y_range'][0]
		
		for _x in range(dijkstra['x_range'][0],dijkstra['x_range'][1]):
			x = _x-dijkstra['x_range'][0]
			
			if not path:
				if (_x,_y) in dijkstra['ignore']:
					print '# ',
					continue
				#else:
				#	print '.',
				_n = str(numbers.clip(abs(int(dijkstra['map'][y,x])),0,41))
				
				if len(_n)==1:
					print '%s ' % _n,
				else:
					print _n,
			else:
				#print path
				if (_x,_y,0) in path:
					print 'o',
				elif (_x,_y) in dijkstra['ignore']:
					print '#',
				else:
					print ' ',
		print

def _main():
	_targets = [{'position': (40,30),'score': 50}]
	MAP = maps.load_map('map1.dat')
	_a = create_dijkstra_map((44,26,2),MAP,_targets)
	_stime = time.time()
	generate_dijkstra_map(_a)
	invert_dijkstra_map(_a)
	print time.time()-_stime
	draw_dijkstra(_a)
	
	_path = pathfinding.path_from_dijkstra((43,30,2),_a,downhill=False)
	draw_dijkstra(_a,path=_path)

_main()
#cProfile.run('_main()','profile.dat')
