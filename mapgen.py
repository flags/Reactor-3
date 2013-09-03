from globals import *

import libtcodpy as tcod

import maputils
import numbers
import effects
import alife
import tiles
import zones
import maps

import logging
import random
import numpy
import copy
import sys
import os

TOWN_DISTANCE = 25
TOWN_SIZE = 160
FOREST_DISTANCE = 25
OPEN_TILES = ['.']
DIRECTION_MAP = {'(-1, 0)': 'left', '(1, 0)': 'right', '(0, -1)': 'top', '(0, 1)': 'bot'}

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
	
	_building_temp = {'open': {'top': _top, 'bot': _bot, 'left': _left, 'right': _right},
	                  'building': copy.deepcopy(building)}
	
	buildings.append(_building_temp)

def load_tiles(file_name, chunk_size):
	with open(os.path.join(TEXT_DIR, file_name), 'r') as f:
		_buildings = []
		_building = []
		_i = 0
		for line in f.readlines():
			_i += 1
			
			if line.startswith('//'):
				continue
			
			if len(line)>1 and (not len(line)-1 == chunk_size or len(_building)>chunk_size):
				logging.debug('Incorrect chunk size (%s) for tile on line %s' % (len(line), _i))
				print 'Incorrect chunk size %s (wanted %s) for tile on line %s' % (len(line)-1, chunk_size, _i)
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

def generate_map(size=(300, 300, 10), detail=5, towns=2, factories=4, forests=1, underground=True, skip_zoning=False):
	""" Size: Both width and height must be divisible by DETAIL.
	Detail: Determines the chunk size. Smaller numbers will generate more elaborate designs.
	towns: Number of towns.
	factories: Decides the amount of factories generated.
	Forests: Number of large forested areas.
	Underground: Flags whether buildings can be constructed beneath the surface.
	"""
	
	map_gen = {'size': size,
		'chunk_size': detail,
		'towns': towns,
		'factories': factories,
		'forests': forests,
		'underground': underground,
		'chunk_map': {},
		'refs': {'factories': [], 'towns': [], 'forests': [], 'roads': []},
		'buildings': load_tiles('buildings.txt', detail),
		'flags': {},
		'map': maps.create_map(size=size)}
	
	#logging.debug('Creating height map...')
	#generate_height_map(map_gen)
	logging.debug('Creating chunk map...')
	generate_chunk_map(map_gen)
	logging.debug('Drawing outlines...')
	generate_outlines(map_gen)	
	logging.debug('Decorating world...')
	decorate_world(map_gen)
	print_chunk_map_to_console(map_gen)
	
	logging.debug('Creating roads...')
	for chunk_key in map_gen['refs']['roads']:
		create_road(map_gen, chunk_key)
	
	logging.debug('Building factories...')
	for _factory in map_gen['refs']['factories']:
		construct_factory(map_gen, _factory)
	
	logging.debug('Building towns...')
	for _town in map_gen['refs']['towns']:
		construct_town(map_gen, _town)
	
	#place_hills(map_gen)
	#print_map_to_console(map_gen)
	
	WORLD_INFO.update(map_gen)
	
	_map_size = maputils.get_map_size(WORLD_INFO['map'])
	MAP_SIZE[0] = _map_size[0]
	MAP_SIZE[1] = _map_size[1]
	MAP_SIZE[2] = _map_size[2]
	
	if not skip_zoning:
		logging.debug('Creating zone map...')
		zones.create_zone_map()
		
		logging.debug('Connecting zone ramps...')
		zones.connect_ramps()
	
	maps.save_map('test2.dat')
	
	return map_gen

def generate_noise_map(size):
	noise = tcod.noise_new(2)
	noise_dx = 0
	noise_dy = 0
	noise_octaves = 3.0
	noise_zoom = 12.0
	
	_noise_map = numpy.zeros(size[:2])
	for y in range(size[1]-1):
		for x in range(size[0]-1):
			f = [noise_zoom * x / (2*size[0]) + noise_dx,
			     noise_zoom * y / (2*size[1]) + noise_dy]
			
			#value = tcod.noise_get_fbm(noise, f, noise_octaves, tcod.NOISE_PERLIN)
			#value = tcod.noise_get_turbulence(noise, f, noise_octaves, tcod.NOISE_PERLIN)
			#value = tcod.noise_get_fbm(noise, f, noise_octaves, tcod.NOISE_SIMPLEX)
			value = tcod.noise_get(noise, f, tcod.NOISE_PERLIN)
			height = int((value + 1.0) / 2.0 * size[2])
			
			for z in range(height):
				_noise_map[x, y] = height
				#callback((x, y, z), value)
				#_tile = tiles.create_tile(random.choice(
				#		[tiles.TALL_GRASS_TILE, tiles.SHORT_GRASS_TILE, tiles.GRASS_TILE]))
				
				#map_gen['map'][x][y][z] = _tile
	
	return _noise_map

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
	logging.debug('Placing roads...')
	place_roads(map_gen)
	
	logging.debug('Placing factories...')
	while len(map_gen['refs']['factories'])<map_gen['factories']:
		place_factory(map_gen)
	
	logging.debug('Placing towns...')
	while len(map_gen['refs']['towns'])<map_gen['towns']:
		place_town(map_gen)
	
	logging.debug('Placing forests...')
	#while len(map_gen['refs']['forests'])<map_gen['forests']:
	place_forest(map_gen)

def place_roads(map_gen, start_pos=None, next_dir=None, turns=-1, can_create=True):
	_start_edge = random.randint(0, 3)
	
	if turns == -1:
		_max_turns = random.randint(3, 6)
	else:
		_max_turns = turns
	
	_pos = start_pos
	_next_dir = next_dir
	
	if not _pos:
		if not _start_edge:
			_pos = [random.randint(0, map_gen['size'][0]/map_gen['chunk_size']), 0]
			_next_dir = (0, 1)
		elif _start_edge == 1:
			_pos = [map_gen['size'][0]/map_gen['chunk_size'], random.randint(0, map_gen['size'][1]/map_gen['chunk_size'])]
			_next_dir = (-1, 0)
		elif _start_edge == 2:
			_pos = [random.randint(0, map_gen['size'][0]/map_gen['chunk_size']), map_gen['size'][1]/map_gen['chunk_size']]
			_next_dir = (0, -1)
		elif _start_edge == 3:
			_pos = [0, random.randint(0, map_gen['size'][1]/map_gen['chunk_size'])]
			_next_dir = (1, 0)
	
	while 1:
		for i in range(40, 40+random.randint(0, 20)):
			_pos[0] += _next_dir[0]
			_pos[1] += _next_dir[1]
			
			if _pos[0] >= map_gen['size'][0]/map_gen['chunk_size']:
				return False
			
			if _pos[1] >= map_gen['size'][1]/map_gen['chunk_size']:
				return False
			
			if _pos[0] < 0:
				return False
			
			if _pos[1] < 0:
				return False
		
			_chunk_key = '%s,%s' % (_pos[0]*map_gen['chunk_size'], _pos[1]*map_gen['chunk_size'])
			map_gen['chunk_map'][_chunk_key]['type'] = 'road'
			map_gen['refs']['roads'].append(_chunk_key)
		
		_possible_next_dirs = []
		if _pos[0]+1<map_gen['size'][0]/map_gen['chunk_size']:
			_possible_next_dirs.append((1, 0))
		
		if _pos[0]-1>0:
			_possible_next_dirs.append((-1, 0))
		
		if _pos[1]+1<map_gen['size'][1]/map_gen['chunk_size']:
			_possible_next_dirs.append((0, 1))
		
		if _pos[1]-1>0:
			_possible_next_dirs.append((0, -1))
		
		for _possible in _possible_next_dirs[:]:
			if not _next_dir[0]+_possible[0] or not _next_dir[1]+_possible[1]:
				_possible_next_dirs.remove(_possible)
		
		while _max_turns and can_create:
			_next_dir = random.choice(_possible_next_dirs)
			_possible_next_dirs.remove(_next_dir)
			
			for _turn in _possible_next_dirs:
				place_roads(map_gen, start_pos=_pos[:], next_dir=_turn, turns=random.randint(0, 3), can_create=False)
			
			break
		
		if _max_turns:
			_max_turns -= 1
			continue
		
		#take rest of _possible_next_dirs and make intersection?

def place_factory(map_gen):
	_existing_factories = map_gen['refs']['factories']
	_avoid_chunk_keys = []
	
	for town in _existing_factories:
		_avoid_chunk_keys.extend(['%s,%s' % (t[0], t[1]) for t in town])
	
	_avoid_chunk_keys.extend(map_gen['refs']['roads'])
	
	while 1:
		while 1:
			_town_chunk = random.choice(map_gen['chunk_map'].values())
			if _town_chunk['pos'][0] == 0 or _town_chunk['pos'][1] == 0 or \
			   _town_chunk['pos'][1] == map_gen['size'][0]+map_gen['chunk_size'] or _town_chunk['pos'][1]+map_gen['chunk_size'] == map_gen['size'][1]:
				continue
			
			break
				
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
		
		_restart = False
		while 1:
			clean_walker(map_gen, _walked, kill_range=(0, 1))
			
			if _walked:
				break
			
			_restart = True
			break
		
		if _restart:
			continue
		
		for pos in _walked:
			map_gen['chunk_map']['%s,%s' % (pos[0], pos[1])]['type'] = 'factory'
		
		map_gen['refs']['factories'].append(_walked)
		break

def place_town(map_gen):
	_avoid_chunk_keys = []
	
	for town in map_gen['refs']['towns']:
		_avoid_chunk_keys.extend(['%s,%s' % (t[0], t[1]) for t in town])
	
	#Find some areas near roads...
	_potential_chunks = []
	_driveways = {}
	for road_chunk_key in map_gen['refs']['roads']:
		_chunk = map_gen['chunk_map'][road_chunk_key]
		for chunk_key in get_neighbors_of_type(map_gen, _chunk['pos'], 'other'):
			_house_chunk = map_gen['chunk_map'][chunk_key]
			_direction = direction_from_key_to_key(map_gen, road_chunk_key, chunk_key)
			_next_chunk_key = '%s,%s' % ((_house_chunk['pos'][0]+(map_gen['chunk_size']*_direction[0])),
			                             (_house_chunk['pos'][1]+(map_gen['chunk_size']*_direction[1])))
			
			if not _next_chunk_key in map_gen['chunk_map']:
				continue
			
			if get_neighbors_of_type(map_gen, map_gen['chunk_map'][_next_chunk_key]['pos'], 'road'):
				continue
			
			if not map_gen['chunk_map'][_next_chunk_key]['type'] == 'other':
				continue
			
			if not _next_chunk_key in _potential_chunks:
				_potential_chunks.append(_next_chunk_key)
				_driveways[_next_chunk_key] = chunk_key
	
	_actual_town_chunks = []
	_max_size = random.randint(30, 40)
	_town_chunks = _potential_chunks[random.randint(0, len(_potential_chunks)-1):]
	for chunk in _town_chunks:
		if random.randint(0, 1):
			continue
		
		if not get_neighbors_of_type(map_gen, map_gen['chunk_map'][_driveways[chunk]]['pos'], 'driveway'):
			create_road(map_gen, _driveways[chunk], ground_tiles=tiles.CONCRETE_FLOOR_TILES, size=1)
			map_gen['chunk_map'][_driveways[chunk]]['type'] = 'driveway'
		
		map_gen['chunk_map'][chunk]['type'] = 'town'
		_actual_town_chunks.append(chunk)
		
		if len(_actual_town_chunks)>_max_size:
			break	
	
	map_gen['refs']['towns'].append(_actual_town_chunks)

def place_hills(map_gen):
	_size = (map_gen['size'][0], map_gen['size'][1], 4)
	_noise_map = generate_noise_map(_size)
	
	for y in range(0, map_gen['size'][1]):
		for x in range(0, map_gen['size'][0]):
			_chunk = map_gen['chunk_map']['%s,%s' % ((x/map_gen['chunk_size'])*map_gen['chunk_size'],
			                                (y/map_gen['chunk_size'])*map_gen['chunk_size'])]
			
			if not _chunk['type'] == 'other':
				continue
			
			for z in range(0, int(_noise_map[y, x])):
				map_gen['map'][x][y][2+z] = tiles.create_tile(random.choice(tiles.GRASS_TILES))

def place_forest(map_gen):
	SMALLEST_FOREST = (80, 80)
	
	_top_left = (random.randint(0, numbers.clip(map_gen['size'][0]-SMALLEST_FOREST[0], SMALLEST_FOREST[0], map_gen['size'][0]-SMALLEST_FOREST[0])),
	             random.randint(0, map_gen['size'][1]-SMALLEST_FOREST[1]))
	_bot_right = (random.randint(_top_left[0]+SMALLEST_FOREST[0], _top_left[0]+(map_gen['size'][0]-_top_left[0])),
	              random.randint(_top_left[1]+SMALLEST_FOREST[1], _top_left[1]+(map_gen['size'][1]-_top_left[1])))
	
	#_size = (_bot_right[0]-_top_left[0],
	#         _bot_right[1]-_top_left[1], 5)
	_size = map_gen['size']
	_top_left = (0, 0)
	_bot_right = (map_gen['size'][0], map_gen['size'][1])
	_noise_map = generate_noise_map(_size)
	
	for y in range(_top_left[1], _bot_right[1]-1):
		for x in range(_top_left[0], _bot_right[0]-1):
			_chunk = map_gen['chunk_map']['%s,%s' % ((x/map_gen['chunk_size'])*map_gen['chunk_size'],
			                                (y/map_gen['chunk_size'])*map_gen['chunk_size'])]
			
			if not _chunk['type'] == 'other' and not _chunk['type'] == 'forest':
				continue
			
			_height = numbers.clip(int(_noise_map[x-_top_left[0],y-_top_left[1]])-2, 0, _size[2])
			if not _height:
				continue
			
			_chunk['type'] = 'forest'
			for z in range(0, _height):
				map_gen['map'][x][y][3+z] = tiles.create_tile(random.choice(tiles.GRASS_TILES))
			#if not random.randint(0, ((_size[2]+1)-_height)*4):
			#	#TODO: Tree tops
			#	for z in range(0, _height):
			#		map_gen['map'][x][y][2+z] = tiles.create_tile(random.choice(tiles.TREE_STUMPS))

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
		
		if chunk_type == 'any' or map_gen['chunk_map'][_next_key]['type'] == chunk_type:
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
	_last_dir = {'dir': None, 'times': 0}
	for i in range(moves/map_gen['chunk_size']):
		_possible_dirs = []
		
		for _dir in _directions[:]:
			_next_pos = [_pos[0]+(_dir[0]*map_gen['chunk_size']), _pos[1]+(_dir[1]*map_gen['chunk_size'])]
			
			if _last_dir['times'] >= 3 and _next_pos == _last_dir['dir']:
				continue

			if _next_pos in _walked:
				continue
			
			if _next_pos[0]<=0 or _next_pos[0]>=map_gen['size'][0]-map_gen['chunk_size'] or _next_pos[1]<=0 or _next_pos[1]>=map_gen['size'][1]-map_gen['chunk_size']:
				continue
			
			if avoid_chunks and alife.chunks.get_distance_to_hearest_chunk_in_list(_next_pos, avoid_chunks) < avoid_chunk_distance:
				continue
			
			_possible_dirs.append(_next_pos)
			
		if not _possible_dirs:
			return False
		
		_chosen_dir = random.choice(_possible_dirs)
		if _chosen_dir == _last_dir['dir']:
			_last_dir['times'] += 1
		else:
			_last_dir['dir'] = _chosen_dir[:]
			_last_dir['times'] += 1
		
		_pos[0] = _chosen_dir[0]
		_pos[1] = _chosen_dir[1]
	
		_walked.append(list(_pos))
	
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
	
	if _k1[0] < _k2[0] and _k1[1] < _k2[1]:
		return (1, 1)
	
	if _k1[0] > _k2[0] and _k1[1] > _k2[1]:
		return (-1, -1)
	
	if _k1[0] < _k2[0] and _k1[1] > _k2[1]:
		return (1, -1)
	
	if _k1[0] > _k2[0] and _k1[1] < _k2[1]:
		return (-1, 1)
	
	raise Exception('Invalid direction.')

def create_road(map_gen, chunk_key, ground_tiles=tiles.CONCRETE_TILES, size=0):
	chunk = map_gen['chunk_map'][chunk_key]
	_directions = []
	
	for neighbor_key in get_neighbors_of_type(map_gen, chunk['pos'], 'road'):
		_directions.append(direction_from_key_to_key(map_gen, chunk_key, neighbor_key))
	
	#for _direction in _directions:
	if len(_directions) == 1 and (0, -1) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if y == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 1 and (0, 1) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if y == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 1 and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if x == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 1 and (-1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if x == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 2 and (-1, 0) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if (y == 0 or y == map_gen['chunk_size']-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				elif y == round(map_gen['chunk_size']/2) and x % 3:
					_tile = tiles.ROAD_STRIPE_2
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 2 and (0, -1) in _directions and (0, 1) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if (x == 0 or x == map_gen['chunk_size']-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 2 and (0, -1) in _directions and (-1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if (y == map_gen['chunk_size']-1 or x == map_gen['chunk_size']-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 3 and (0, -1) in _directions and (-1, 0) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if y == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 3 and (0, 1) in _directions and (-1, 0) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if y == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 3 and (0, -1) in _directions and (0, 1) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if x == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 3 and (0, -1) in _directions and (0, 1) in _directions and (-1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if x == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
				else:
					_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	elif len(_directions) == 4:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				_tile = random.choice(ground_tiles)
					
				map_gen['map'][chunk['pos'][0]+x][chunk['pos'][1]+y][2] = maps.create_tile(_tile)
	
	return _directions

def construct_factory(map_gen, town):
	_open = ['%s,%s' % (pos[0], pos[1]) for pos in town[:]]
	
	while _open:
		_start_key = _open.pop(random.randint(0, len(_open)-1))
		_occupied_chunks = random.randint(1, len(_open)+1)
		_build_on_chunks = [_start_key]
		_door = {'chunk': None, 'direction': None, 'created': False}
		
		while len(_build_on_chunks) < _occupied_chunks:
			_center_chunk = random.choice(_build_on_chunks)
			
			_possible_next_chunk = random.choice(get_neighbors_of_type(map_gen, map_gen['chunk_map'][_center_chunk]['pos'], 'factory'))
			if _possible_next_chunk in _build_on_chunks:
				continue
			
			_build_on_chunks.append(_possible_next_chunk)
		
		if len(_build_on_chunks) == 1:
			break
		
		_make_door = False
		for _chunk in _build_on_chunks:
			if _chunk in _open:
				_open.remove(_chunk)
			
			_directions = []
			_avoid_directions = []
			for _neighbor in get_neighbors_of_type(map_gen, map_gen['chunk_map'][_chunk]['pos'], 'any'):
				if _neighbor in _build_on_chunks:
					_directions.append(str(direction_from_key_to_key(map_gen, _chunk, _neighbor)))
				else:
					if _neighbor in _open:
						_open.remove(_neighbor)
						
						if not _door['chunk']:
							_door['chunk'] = _neighbor[:]
							_door['direction'] = str(direction_from_key_to_key(map_gen, _chunk, _neighbor))
							_directions.append(str(direction_from_key_to_key(map_gen, _chunk, _neighbor)))
							continue
					
					_avoid_directions.append(str(direction_from_key_to_key(map_gen, _chunk, _neighbor)))
			
			_possible_buildings = []
			_direction_keys = [DIRECTION_MAP[d] for d in _directions]
			_avoid_direction_keys = [DIRECTION_MAP[d] for d in _avoid_directions]
			
			for building in map_gen['buildings']:
				_continue = False
				for _dir in _direction_keys:
					if not building['open'][_dir]:
						_continue = True
						break
				
				if _continue:
					continue
				
				for _dir in _avoid_direction_keys:
					if building['open'][_dir]:
						_continue = True
						break
				
				if _continue:
					continue
				
				_possible_buildings.append(building['building'])
			
			_chunk_pos = map_gen['chunk_map'][_chunk]['pos']
			_building = random.choice(_possible_buildings)
			for _y in range(map_gen['chunk_size']):
				y = _chunk_pos[1]+_y
				for _x in range(map_gen['chunk_size']):
					x = _chunk_pos[0]+_x
					
					for i in range(3):
						if _building[_y][_x] == '#':
							map_gen['map'][x][y][2+i] = tiles.create_tile(tiles.WALL_TILE)
						elif (not i or i == 2) and _building[_y][_x] == '.':
							map_gen['map'][x][y][2+i] = tiles.create_tile(random.choice(tiles.CONCRETE_FLOOR_TILES))
							
							if not i and random.randint(0, 500) == 500:
								effects.create_light((x, y, 2), (255, 0, 255), 5, 0.1)

def construct_town(map_gen, town):
	#_houses = []
	_taken = []
	for chunk_key in town:
		if chunk_key in _taken:
			continue
		
		_chunk = map_gen['chunk_map'][chunk_key]
		_house = [chunk_key]
		_house_dirs = {}
		while 1:
			_neighbors = get_neighbors_of_type(map_gen, _chunk['pos'], 'town')
			_added = False
			for neighbor_key in _neighbors:
				if not neighbor_key in _house:
					_house.append(neighbor_key)
					_added = True
			
			if not _added:
				break
		
		#_houses.append(_house)
		_taken.extend(_house)
		
		for chunk_key in _house:
			_avoid_directions = []
			_directions = []
			_chunk = map_gen['chunk_map'][chunk_key]
			for neighbor_key in get_neighbors_of_type(map_gen, _chunk['pos'], 'any'):
				if not neighbor_key in _house:
					_avoid_directions.append(DIRECTION_MAP[str(direction_from_key_to_key(map_gen, chunk_key, neighbor_key))])
					continue
				
				if map_gen['chunk_map'][neighbor_key]['type'] == 'town':
					_directions.append(DIRECTION_MAP[str(direction_from_key_to_key(map_gen, chunk_key, neighbor_key))])
		
			_possible_tiles = []
			for building in map_gen['buildings']:
				_continue = False
				for _dir in _directions:
					if not building['open'][_dir]:
						_continue = True
						break
				
				if _continue:
					continue
				
				for _dir in _avoid_directions:
					if building['open'][_dir]:
						_continue = True
						break
				
				if _continue:
					continue
				
				_possible_tiles.append(building['building'])
			
			_building = random.choice(_possible_tiles)
			for _y in range(map_gen['chunk_size']):
				y = _chunk['pos'][1]+_y
				for _x in range(map_gen['chunk_size']):
					x = _chunk['pos'][0]+_x
					
					for i in range(3):
						if _building[_y][_x] == '#':
							map_gen['map'][x][y][2+i] = tiles.create_tile(tiles.WALL_TILE)
						elif (not i or i == 2) and _building[_y][_x] == '.':
							map_gen['map'][x][y][2+i] = tiles.create_tile(random.choice(tiles.CONCRETE_FLOOR_TILES))
							
							if not i and random.randint(0, 500) == 500:
								effects.create_light((x, y, 2), (255, 0, 255), 5, 0.1)

def decorate_world(map_gen):
	#TODO: Fences
	
	#backyards
	for town in map_gen['refs']['towns']:
		_backyard = []
		for chunk_key in town:
			_chunk = map_gen['chunk_map'][chunk_key]
			for neighbor in get_neighbors_of_type(map_gen, _chunk['pos'], 'other', diagonal=True):
				if not get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor]['pos'], 'driveway', diagonal=False):
					_backyard.append(neighbor)
		
		for chunk_key in _backyard:
			map_gen['chunk_map'][chunk_key]['type'] = 'backyard'

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
	generate_map(skip_zoning=True)