from globals import *

import alife
import tiles
import maps

import logging
import random
import copy
import os

TOWN_DISTANCE = 35
TOWN_SIZE = 80
FOREST_DISTANCE = 25
OPEN_TILES = ['.', 'd']

tiles.create_all_tiles()

def create_building(buildings, building, chunk_size):
	_top = False
	_bot = False
	_left = False
	_right = False
	
	for y in range(chunk_size):
		for x in range(chunk_size):
			_tile = building[y][x]
			
			if x == 0 and (y>0 or y<chunk_size) and _tile in OPEN_TILES:
				_left = True
			
			if x == chunk_size-1 and (y>0 or y<chunk_size) and _tile in OPEN_TILES:
				_right = True
			
			if y == 0 and (x>0 or x<chunk_size) and _tile in OPEN_TILES:
				_top = True
			
			if y == chunk_size-1 and (x>0 or x<chunk_size) and _tile in OPEN_TILES:
				_bot = True
	
	_building_temp = copy.deepcopy(building)
	
	if _top:
		buildings['top'].append(_building_temp)
	
	if _bot:
		buildings['bot'].append(_building_temp)
	
	if _left:
		buildings['left'].append(_building_temp)
	
	if _right:
		buildings['right'].append(_building_temp)

def load_buildings(chunk_size):
	with open(os.path.join(TEXT_DIR, 'buildings.txt'), 'r') as f:
		_buildings = {'top': [], 'bot': [], 'left': [], 'right': []}
		_building = []
		_i = 0
		for line in f.readlines():
			_i += 1
			
			if line.startswith('//'):
				continue
			
			if len(line)>1 and not len(line)-1 == chunk_size:
				logging.debug('Incorrect chunk size (%s) for building on line %s' % (len(line), _i))
				print 'Incorrect chunk size %s (wanted %s) for building on line %s' % (len(line)-1, chunk_size, _i)
				continue
			
			line = line.rstrip()
			
			if line:
				_building.append(line)
			elif _building:
				create_building(_buildings, _building, chunk_size)
				_building = []
		
		if _building:
			create_building(_buildings, _building, chunk_size)
	
	return _buildings

def generate_map(size=(125, 125, 10), detail=5, towns=4, forests=1, underground=True):
	""" Size: Both width and height must be divisible by DETAIL.
	Detail: Determines the chunk size. Smaller numbers will generate more elaborate designs.
	Towns: Decides the amount of towns generated.
	Forests: Number of large forested areas.
	Underground: Flags whether buildings can be constructed beneath the surface.
	"""
	
	map_gen = {'size': size,
		'chunk_size': detail,
		'towns': towns,
		'forests': forests,
		'underground': underground,
		'chunk_map': {},
		'refs': {'towns': [], 'forests': []},
		'map': maps.create_map(size=size)}
	
	logging.debug('Grabbing buildings...')
	_buildings = load_buildings(detail)
	print _buildings
	
	logging.debug('Creating chunk map...')
	generate_chunk_map(map_gen)
	logging.debug('Drawing outlines...')
	generate_outlines(map_gen)
	print_chunk_map_to_console(map_gen)
	
	logging.debug('Building towns...')
	for _town in map_gen['refs']['towns']:
		construct_town(map_gen, _town)
	#print_map_to_console(map_gen)
	
	return map_gen

def generate_chunk_map(map_gen):
	for y1 in xrange(0, map_gen['size'][1], map_gen['chunk_size']):
		for x1 in xrange(0, map_gen['size'][0], map_gen['chunk_size']):
			_chunk_key = '%s,%s' % (x1, y1)
			
			map_gen['chunk_map'][_chunk_key] = {'pos': (x1, y1),
				'ground': [],
				'life': [],
				'items': [],
				'control': {},
				'neighbors': [],
				'reference': None,
				'last_updated': None,
				'digest': None,
				'type': 'other'}
			
def generate_outlines(map_gen):
	logging.debug('Placing towns...')
	while len(map_gen['refs']['towns'])<map_gen['towns']:
		place_town(map_gen)
	
	logging.debug('Placing forests...')
	while len(map_gen['refs']['forests'])<map_gen['forests']:
		place_forest(map_gen)

def place_town(map_gen):
	_existing_towns = map_gen['refs']['towns']
	_avoid_chunk_keys = []
	
	for town in _existing_towns:
		_avoid_chunk_keys.extend(['%s,%s' % (t[0], t[1]) for t in town])
	
	while 1:
		_town_chunk = random.choice(map_gen['chunk_map'].values())
				
		if _avoid_chunk_keys and alife.chunks.get_distance_to_hearest_chunk_in_list(_town_chunk['pos'], _avoid_chunk_keys) < TOWN_DISTANCE:
			continue
		
		_walked = walker(map_gen,
			_town_chunk['pos'],
		     TOWN_SIZE,
			allow_diagonal_moves=False,
			avoid_chunks=_avoid_chunk_keys,
			avoid_chunk_distance=TOWN_DISTANCE)
			
		if not _walked:
			continue
		
		clean_walker(map_gen, _walked, kill_range=(0, 1))
		
		for pos in _walked:
			map_gen['chunk_map']['%s,%s' % (pos[0], pos[1])]['type'] = 'town'
		
		map_gen['refs']['towns'].append(_walked)
		break

def place_forest(map_gen):
	_existing_chunks = map_gen['refs']['forests']
	_avoid_chunk_keys = []
	
	for chunk in _existing_chunks:
		_avoid_chunk_keys.extend(['%s,%s' % (c[0], c[1]) for c in chunk])
	
	while 1:
		_chunk = random.choice(map_gen['chunk_map'].values())
				
		if _avoid_chunk_keys and alife.chunks.get_distance_to_hearest_chunk_in_list(_chunk['pos'], _avoid_chunk_keys) < FOREST_DISTANCE:
			continue
		
		_walked = walker(map_gen,
			_chunk['pos'],
		     60,
			allow_diagonal_moves=False,
			avoid_chunks=_avoid_chunk_keys,
			avoid_chunk_distance=FOREST_DISTANCE)
			
		if not _walked:
			continue
		
		for pos in _walked:
			map_gen['chunk_map']['%s,%s' % (pos[0], pos[1])]['type'] = 'forest'
		
		map_gen['refs']['forests'].append(_walked)
		break

def get_neighbors_of_type(map_gen, pos, chunk_type, diagonal=False, return_keys=True):
	_directions = [(0, -1), (-1, 0), (1, 0), (0, 1)]
	_keys = []
	_neighbors = 0
	
	if diagonal:
		_directions.extend([(-1, -1), (1, 1), (-1, 1), (1, 1)])
	
	for _dir in _directions:
		_next_pos = [pos[0]+(_dir[0]*map_gen['chunk_size']), pos[1]+(_dir[1]*map_gen['chunk_size'])]
		_next_key = '%s,%s' % (_next_pos[0], _next_pos[1])
		
		if _next_pos[0]<0 or _next_pos[0]>=map_gen['size'][0] or _next_pos[1]<0 or _next_pos[1]>=map_gen['size'][1]:
			continue
		
		if map_gen['chunk_map'][_next_key]['type'] == chunk_type:
			_keys.append(_next_key)
			_neighbors += 1
	
	if return_keys:
		return _keys
	
	return _neighbors

def walker(map_gen, pos, moves, density=5, allow_diagonal_moves=True, avoid_chunks=[], avoid_chunk_distance=0):
	_pos = list(pos)
	_directions = [(0, -1), (-1, 0), (1, 0), (0, 1)]
	
	if allow_diagonal_moves:
		_directions.extend([(-1, -1), (1, 1), (-1, 1), (1, 1)])
	
	_walked = []
	
	for i in range(moves/map_gen['chunk_size']):
		_possible_dirs = []
		
		for _dir in _directions[:]:
			_next_pos = [_pos[0]+(_dir[0]*map_gen['chunk_size']), _pos[1]+(_dir[1]*map_gen['chunk_size'])]

			if _next_pos in _walked:
				continue
			
			if _next_pos[0]<0 or _next_pos[0]>=map_gen['size'][0] or _next_pos[1]<0 or _next_pos[1]>=map_gen['size'][1]:
				continue
			
			if avoid_chunks and alife.chunks.get_distance_to_hearest_chunk_in_list(_next_pos, avoid_chunks) < avoid_chunk_distance:
				continue
			
			_possible_dirs.append(_next_pos)
			
		if not _possible_dirs:
			return False
		
		_chosen_dir = random.choice(_possible_dirs)
		
		_pos[0] = _chosen_dir[0]
		_pos[1] = _chosen_dir[1]
	
		#print _pos,_chosen_dir
		_walked.append(list(_pos))
	
	#print _walked
	return _walked

def clean_walker(map_gen, walker, kill_range=(-2, -1)):
	while 1:
		_changed = False
		
		for pos in walker[:]:
			_num = 0
			for neighbor in get_neighbors_of_type(map_gen, pos, 'other'):
				_neighbor_pos = list(map_gen['chunk_map'][neighbor]['pos'])
				if _neighbor_pos in walker:
					_num += 1
			
			if _num in range(kill_range[0], kill_range[1]+1):
				walker.remove(pos)
				_changed = True
		
		if not _changed:
			break

def direction_from_key_to_key(map_gen, key1, key2):
	_k1 = map_gen['chunk_map'][key1]['pos']
	_k2 = map_gen['chunk_map'][key2]['pos']
	
	if _k1 == _k2:
		return (0, 0)
	
	if _k1[0] == _k2[0] and _k1[1] < _k2[1]:
		return (0, 1)
	
	if _k1[0] == _k2[0] and _k1[1] > _k2[1]:
		return (0, -1)	
	
	if _k1[0] < _k2[0] and _k1[1] == _k2[1]:
		return (1, 0)
	
	if _k1[0] > _k2[0] and _k1[1] == _k2[1]:
		return (-1, 0)
	
	raise Exception('Invalid direction.')

def construct_town(map_gen, town):
	_open = ['%s,%s' % (pos[0], pos[1]) for pos in town[:]]
	
	while _open:
		_start_key = _open.pop(random.randint(0, len(_open)-1))
		
		_occupied_chunks = random.randint(1, len(town))
		_build_on_chunks = [_start_key]
		
		while len(_build_on_chunks) < _occupied_chunks:
			_center_chunk = random.choice(_build_on_chunks)
			
			_possible_next_chunk = random.choice(get_neighbors_of_type(map_gen, map_gen['chunk_map'][_center_chunk]['pos'], 'town'))
			if _possible_next_chunk in _build_on_chunks:
				continue
			
			_build_on_chunks.append(_possible_next_chunk)
		
		for _chunk in _build_on_chunks:
			if _chunk in _open:
				_open.remove(_chunk)
			
			for _neighbor in get_neighbors_of_type(map_gen, map_gen['chunk_map'][_chunk]['pos'], 'town'):
				if not _neighbor in _build_on_chunks:
					continue

#def construct_town(map_gen, town):
	#_open = ['%s,%s' % (pos[0], pos[1]) for pos in town[:]]
	#_current_building = _open[:]
	
	#while _open:
		#_start_key = _open.pop(random.randint(0, len(_open)-1))
		
		##Determine size of building...
		#_occupied_chunks = random.randint(1, len(town))
		#_build_on_chunks = [_start_key]
		
		#while len(_build_on_chunks) < _occupied_chunks:
			##Find a chunk to focus on and check its neighbors
			#_center_chunk = random.choice(_build_on_chunks)
			
			#_possible_next_chunk = random.choice(get_neighbors_of_type(map_gen, map_gen['chunk_map'][_center_chunk]['pos'], 'town'))
			#if _possible_next_chunk in _build_on_chunks:
				#continue
			
			#_build_on_chunks.append(_possible_next_chunk)
		
		#for _chunk in _build_on_chunks:
			#if _chunk in _open:
				#_open.remove(_chunk)
		
		#_connections = {chunk: [] for chunk in _build_on_chunks}
		#_built = []
		#while _build_on_chunks:
			#if not _built:
				#_building_on = random.choice(_build_on_chunks)
			
			#_existing_connections = []
			#_future_connections = []
			
			#for _neighbor in get_neighbors_of_type(map_gen, map_gen['chunk_map'][_building_on]['pos'], 'town'):
				#if not _neighbor in _current_building:
					#continue
				
				##if not _neighbor in _build_on_chunks:
				##	if _neighbor in _open:
				##		_open.remove(_neighbor)
				##		#continue
				
				##If a neighbor has already been worked on, start working where they left off
				#if _neighbor in _built:
					#_existing_connections.append(_neighbor)
				
				#_future_connections.append(_neighbor)
			
			##If no writers remain we need to find out where features should be placed.
			##We do this by looking at _future_connections and drawing lines to these
			#_directions_to_future_connections = {}
			#for _connection in _future_connections:
				#_direction = direction_from_key_to_key(map_gen, _building_on, _connection)
				#_directions_to_future_connections[_connection] = _direction
			
			##print _directions_to_future_connections.values()
			
			##This is surrounded by rooms... no stones needed
			#if len(_directions_to_future_connections) == 4:
				#_build_on_chunks.remove(_building_on)
				#continue
			
			##Place corner stones
			#_edges = [d for d in [(0, -1), (-1, 0), (1, 0), (0, 1)] if not d in _directions_to_future_connections.values()]
			
			#_cornerstones = []
			#for _dir in _edges:
				#_stone_pos = [0, 0]
				
				#if _dir[0]<0 and _dir[1] == 0:
					#_stone_pos[0] -= 1
				#elif _dir[0]>0 and _dir[1] == 0:
					#_stone_pos[0] += 1
				#elif _dir[0] == 0 and _dir[1] < 0:
					#_stone_pos[1] -= 1
				#elif _dir[0] == 0 and _dir[1] > 0:
					#_stone_pos[1] += 1
				
				#_cornerstones.append(tuple(_stone_pos))
			
			#_pos = map_gen['chunk_map'][_building_on]['pos']
			#for _stone in _cornerstones:
				#if _stone == (-1, 0):
					#for i in range(0, map_gen['chunk_size']+1):
						#map_gen['map'][_pos[0]][_pos[1]+i][2] = tiles.create_tile(tiles.WALL_TILE)
				#elif _stone == (1, 0):
					#for i in range(0, map_gen['chunk_size']+1):
						#map_gen['map'][_pos[0]+map_gen['chunk_size']][_pos[1]+i][2] = tiles.create_tile(tiles.WALL_TILE)
				#elif _stone == (0, -1):
					#for i in range(0, map_gen['chunk_size']+1):
						#map_gen['map'][_pos[0]+i][_pos[1]][2] = tiles.create_tile(tiles.WALL_TILE)
				#elif _stone == (0, 1):
					#for i in range(0, map_gen['chunk_size']+1):
						#map_gen['map'][_pos[0]+i][_pos[1]+map_gen['chunk_size']][2] = tiles.create_tile(tiles.WALL_TILE)
			
			#_build_on_chunks.remove(_building_on)

MAP_KEY = {'o': '.',
           't': 't'}

def print_chunk_map_to_console(map_gen):
	for y1 in xrange(0, map_gen['size'][1], map_gen['chunk_size']):
		for x1 in xrange(0, map_gen['size'][0], map_gen['chunk_size']):
			_chunk_key = '%s,%s' % (x1, y1)
			_key = map_gen['chunk_map'][_chunk_key]['type'][0]
			
			if _key in  MAP_KEY:
				print MAP_KEY[_key],
			else:
				print _key,
		
		print 

def print_map_to_console(map_gen):
	for y1 in xrange(0, map_gen['size'][1]):
		for x1 in xrange(0, map_gen['size'][0]):
			print tiles.get_raw_tile(map_gen['map'][x1][y1][2])['icon'],
		
		print

if __name__ == '__main__':
	generate_map()