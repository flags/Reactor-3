#Accept walls and understand unpassable terrain
#Easily recalcuate map

from numbers import *
import numpy
import maps

def create_dijkstra_map(center,source_map,targets):
	#Calculate the maximum size of the of the map by testing distances to all targets
	_farthest_distance = 0
	
	for target in targets:
		_dist = distance(center,target['position'])
	
		if _dist>_farthest_distance:
			_farthest_distance = _dist+1

	_min_x = clip(center[0]-(_farthest_distance),0,MAP_SIZE[0])
	_max_x = clip(center[0]+(_farthest_distance),0,MAP_SIZE[0])
	_min_y = clip(center[1]-(_farthest_distance),0,MAP_SIZE[1])
	_max_y = clip(center[1]+(_farthest_distance),0,MAP_SIZE[1])
	_map = numpy.ones((_max_y,_max_x))
	_ignore = []
	
	for target in targets:
		_map[target['position'][1]-_min_y,target['position'][0]-_min_x] = 0
	
	#TODO: This number controls how much detail we get in the map
	_map*=9
	
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
	
	while 1:
		#print 'running'
		_orig_map = _map.copy()
		
		for _x in range(_min_x,_max_x):
			for _y in range(_min_y,_max_y):				
				if (_x,_y) in _target_positions or (_x,_y) in dijkstra['ignore']:
					continue
				
				_lowest_score = 9000
				
				for x_mod in range(-1,2):
					_map_x_pos = (_x-_min_x)+x_mod
					
					if 0>_map_x_pos or _map_x_pos>=_map.shape[1]-1:
						continue
					
					for y_mod in range(-1,2):
						if (x_mod,y_mod) == (0,0) or (_x+x_mod,_y+y_mod) in dijkstra['ignore']:
							continue
						
						_map_y_pos = (_y-_min_y)+y_mod
						
						if 0>_map_y_pos or _map_y_pos>=_map.shape[0]-2:	
							continue
						
						if _orig_map[_y-_min_y,_x-_min_x]-_orig_map[_map_y_pos,_map_x_pos]>=2:
							_lowest_score = _orig_map[_map_y_pos,_map_x_pos]+1
				
				if _lowest_score < 9000:
					_map[_y-_min_y,_x-_min_x] = _lowest_score
				
		if numpy.array_equal(_map,_orig_map):
			break

def draw_dijkstra(dijkstra):
	for _y in range(dijkstra['y_range'][0],dijkstra['y_range'][1]):
		y = _y-dijkstra['y_range'][0]
		
		for _x in range(dijkstra['x_range'][0],dijkstra['x_range'][1]):
			x = _x-dijkstra['x_range'][0]
			
			if (_x,_y) in dijkstra['ignore']:
				print '#',
				continue
			#else:
			#	print '.',
			print int(dijkstra['map'][y,x]),
		
		print

if __name__ == "__main__":
	_targets = [{'position': (53,29),'score': 50}]
	MAP = maps.load_map('map1.dat')
	_a = create_dijkstra_map((50,25,2),MAP,_targets)
	generate_dijkstra_map(_a)
	#_a = create_flee_map(_a)
	#_path = pathfinding.path_from_dijkstra((46,28,2),_a,downhill=True)
	#print _path
	draw_dijkstra(_a)
