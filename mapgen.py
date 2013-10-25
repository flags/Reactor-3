from globals import *

import libtcodpy as tcod

import maputils
import language
import drawing
import numbers
import effects
import items
import alife
import tiles
import zones
import maps
import smp

import cProfile
import logging
import random
import numpy
import time
import copy
import sys
import os

TOWN_DISTANCE = 60*5
TOWN_SIZE = 160
FOREST_DISTANCE = 10
FIELD_SIZE_RANGE = [45, 46]
FIELD_DISTANCE = 30*5
OPEN_TILES = ['.']
DIRECTION_MAP = {'(-1, 0)': 'left', '(1, 0)': 'right', '(0, -1)': 'top', '(0, 1)': 'bot'}
ROOM_TYPES = {'bedroom': {'required': True, 'floor_tiles': tiles.DARK_GREEN_FLOOR_TILES},
              'bathroom': {'required': True, 'floor_tiles': tiles.BLUE_FLOOR_TILES},
              'kitchen': {'floor_tiles': tiles.BROWN_FLOOR_TILES},
              'dining_room': {'floor_tiles': tiles.WHITE_TILE_TILES}}

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
			
			#print _tile,
		
		#print
	
	_building_temp = {'open': {'top': _top, 'bot': _bot, 'left': _left, 'right': _right},
	                  'building': copy.deepcopy(building)}
	
	#for key in _building_temp['open']:
	#	if _building_temp['open'][key]:
	#		print key
	
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

def create_tile(map_gen, x, y, z, tile):
	map_gen['map'][x][y][z] = tiles.create_tile(tile)
	
	_chunk = map_gen['chunk_map'][alife.chunks.get_chunk_key_at((x, y))]
	if z > _chunk['max_z']:
		_chunk['max_z'] = z

def generate_map(size=(450, 450, 10), detail=5, towns=2, factories=1, forests=1, underground=True, skip_zoning=False, skip_chunking=False):
	""" Size: Both width and height must be divisible by DETAIL.
	Detail: Determines the chunk size. Smaller numbers will generate more elaborate designs.
	towns: Number of towns.
	factories: Decides the amount of factories generated.
	Forests: Number of large forested areas.
	Underground: Flags whether buildings can be constructed beneath the surface.
	"""
	
	#smp.init()
	
	map_gen = {'name': '%s.dat' % time.time(),
		'size': size,
		'chunk_size': detail,
		'towns': towns,
		'factories': factories,
		'forests': forests,
		'underground': underground,
		'chunk_map': {},
		'refs': {'factories': [], 'towns': {}, 'forests': [], 'roads': [], 'town_seeds': []},
		'buildings': load_tiles('buildings.txt', detail),
		'flags': {},
		'map': maps.create_map(size=size),
		'settings': {'back yards': False, 'town size': 15}}
	
	WORLD_INFO['chunk_map'] = map_gen['chunk_map']
	
	#logging.debug('Creating height map...')
	#generate_height_map(map_gen)
	logging.debug('Creating chunk map...')
	generate_chunk_map(map_gen)
	logging.debug('Drawing outlines...')
	generate_outlines(map_gen)	
	
	logging.debug('Creating roads...')
	for chunk_key in map_gen['refs']['roads']:
		create_road(map_gen, chunk_key)
	
	#logging.debug('Building factories...')
	#for _factory in map_gen['refs']['factories']:
		#construct_factory(map_gen, _factory)
	
	logging.debug('Building towns...')
	for _town in map_gen['refs']['towns']:
		construct_town(map_gen, map_gen['refs']['towns'][_town]['chunks'])
	
	##place_hills(map_gen)
	##print_map_to_console(map_gen)
	
	clean_chunk_map(map_gen, 'driveway', chunks_of_type='town', minimum_chunks=1)
	clean_chunk_map(map_gen, 'wall', chunks_of_type='wall', minimum_chunks=1)
	
	#print_chunk_map_to_console(map_gen)
	
	map_gen['items'] = ITEMS
	WORLD_INFO.update(map_gen)
	
	_map_size = maputils.get_map_size(WORLD_INFO['map'])
	MAP_SIZE[0] = _map_size[0]
	MAP_SIZE[1] = _map_size[1]
	MAP_SIZE[2] = _map_size[2]
	
	if not skip_zoning:
		logging.debug('Creating zone map...')
		zones.create_zone_map()
		#smp.create_zone_maps()
		
		logging.debug('Connecting zone ramps...')
		zones.connect_ramps()
	
	if not skip_chunking:
		maps.update_chunk_map()
		maps.smooth_chunk_map()
		maps.generate_reference_maps()
	
	items.save_all_items()
	maps.save_map(map_gen['name'])
	items.reload_all_items()
	
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
				#_tile = tiles.create_tile(map_gen, random.choice(
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
				'flags': {},
				'type': 'other',
				'max_z': 2}
			
def generate_outlines(map_gen):
	logging.debug('Placing roads and towns...')
	place_road(map_gen, turnoffs=map_gen['towns']-1, length=(15*map_gen['towns'], 35*map_gen['towns']), width=2)
	
	#logging.debug('Placing factories...')
	#while len(map_gen['refs']['factories'])<map_gen['factories']:
	#	place_factory(map_gen)
	
	logging.debug('Placing towns...')
	for town_seed_chunk in map_gen['refs']['town_seeds']:
		place_town(map_gen, start_chunk_key=town_seed_chunk)
	
	for chunk_key in clean_chunk_map(map_gen, 'town', minimum_chunks=1):
		for town in map_gen['refs']['towns'].values():
			if chunk_key in town['chunks']:
				town['chunks'].remove(chunk_key)
	
	logging.debug('Occupying empty spaces...')
	fill_empty_spaces(map_gen)
	
	logging.debug('Decorating world...')
	decorate_world(map_gen)
	
	logging.debug('Placing forests...')
	while len(map_gen['refs']['forests'])<map_gen['forests']:
		map_gen['refs']['forests'].append(place_forest(map_gen))

def place_road(map_gen, length=(15, 25), start_pos=None, next_dir=None, turnoffs=1, turns=-1, width=1, can_create=0):
	_start_edge = random.randint(0, 3)
	
	if turns == -1:
		_max_turns = random.randint(3, 6)
	else:
		_max_turns = turns
	
	_road_segments = range(random.randint(length[0], length[1]))
	_town_segments = []
	for i in range(turnoffs):
		_segment = random.randint(int(len(_road_segments)*(i/float(turnoffs))), int(len(_road_segments)*(i+1/float(turnoffs))))
		_town_segments.append(_segment)
	
	_pos = start_pos
	_next_dir = next_dir
	
	if start_pos:
		_chunk_key = '%s,%s' % ((start_pos[0]/map_gen['chunk_size'])*map_gen['chunk_size'],
		                        (start_pos[1]/map_gen['chunk_size'])*map_gen['chunk_size'])
	
	if not _pos:
		if not _start_edge:
			_pos = [random.randint(0, map_gen['size'][0]/map_gen['chunk_size']), -1]
			_next_dir = (0, 1)
		elif _start_edge == 1:
			_pos = [map_gen['size'][0]/map_gen['chunk_size'], random.randint(0, map_gen['size'][1]/map_gen['chunk_size'])]
			_next_dir = (-1, 0)
		elif _start_edge == 2:
			_pos = [random.randint(0, map_gen['size'][0]/map_gen['chunk_size']), map_gen['size'][1]/map_gen['chunk_size']]
			_next_dir = (0, -1)
		elif _start_edge == 3:
			_pos = [-1, random.randint(0, map_gen['size'][1]/map_gen['chunk_size'])]
			_next_dir = (1, 0)
	
	while 1:
		for i in _road_segments:
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
		
			for _i in range(1, 1+width):
				_x = 0
				_y = 0
				if _next_dir[0]:
					_y = _i-1
				elif _next_dir[1]:
					_x = _i-1
				
				if (_pos[0]+_x)*map_gen['chunk_size']>=MAP_SIZE[0] or (_pos[0]+_x)*map_gen['chunk_size']<0 or (_pos[1]+_y)*map_gen['chunk_size']>=MAP_SIZE[1] or (_pos[1]+_y)*map_gen['chunk_size']<0:
					continue
				
				_chunk_key = '%s,%s' % ((_pos[0]+_x)*map_gen['chunk_size'], (_pos[1]+_y)*map_gen['chunk_size'])
				map_gen['chunk_map'][_chunk_key]['type'] = 'road'
				map_gen['refs']['roads'].append(_chunk_key)
			
			if i in _town_segments:
				_possible_next_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
				_possible_next_dirs.remove(_next_dir)
				
				place_road(map_gen, start_pos=_pos[:], turnoffs=0, length=(10, 20), next_dir=random.choice(_possible_next_dirs), turns=3, can_create=3, width=1)
		
		if _max_turns:
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
			
			_next_dir = random.choice(_possible_next_dirs)
			
			if can_create:
				
				map_gen['refs']['town_seeds'].append(_chunk_key)
				
				if can_create>1:
					place_road(map_gen, start_pos=_pos[:], turnoffs=0, length=(5, 10), next_dir=random.choice(_possible_next_dirs), turns=can_create-1, can_create=can_create-1, width=1)
				
				can_create -= 1
				
				#if _max_turns:
				#	print 'possible', _possible_next_dirs
			
				#_possible_next_dirs.remove(_next_dir)
					
				#_turn = random.choice(_possible_next_dirs)
				#	place_road(map_gen, start_pos=_pos[:], next_dir=_turn, turns=3, can_create=True, width=1)
			
			_max_turns -= 1
		else:
			break
		
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
				
		if _avoid_chunk_keys and alife.chunks.get_distance_to_nearest_chunk_in_list(_town_chunk['pos'], _avoid_chunk_keys) < TOWN_DISTANCE:
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

def place_town(map_gen, start_chunk_key=None):
	_avoid_chunk_keys = []
	_chunks = []
	_driveways = {}
	
	for town in map_gen['refs']['towns'].values():
		_avoid_chunk_keys.extend(['%s,%s' % (t[0], t[1]) for t in town['chunks']])
	
	#Find some areas near roads...
	if start_chunk_key:
		_start_chunk = map_gen['chunk_map'][start_chunk_key]
		for road_chunk_key in get_all_connected_chunks_of_type(map_gen, start_chunk_key, 'road'):
			_road_chunk = map_gen['chunk_map'][road_chunk_key]
			
			if numbers.distance(_start_chunk['pos'], _road_chunk['pos'])<map_gen['settings']['town size']*WORLD_INFO['chunk_size']:
				_chunks.append(_road_chunk)
	else:
		logging.warning('No given start chunk for town. This might look weird...')
		for road_chunk_key in map_gen['refs']['roads']:
			_chunks.append(map_gen['chunk_map'][road_chunk_key])
			
	#print _chunks
	_potential_chunks = []
	for chunk in _chunks:
		for chunk_key in get_neighbors_of_type(map_gen, chunk['pos'], 'other'):
			_house_chunk = map_gen['chunk_map'][chunk_key]
			_direction = direction_from_key_to_key(map_gen, '%s,%s' % (chunk['pos'][0], chunk['pos'][1]), chunk_key)
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
				_driveways[_next_chunk_key] = chunk_key[:]
	
	_actual_town_chunks = []
	_max_size = random.randint(30, 40)
	_town_chunks = _potential_chunks#[:random.randint(0, numbers.clip(len(_potential_chunks)-1, 0, 60))]
	for chunk in _town_chunks:
		_skip = False
		for neighbor_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk]['pos'], 'town', diagonal=True):
			if not neighbor_key in _town_chunks:
				_skip = True
				break
		
		if _skip:
			continue
		
		if len(get_all_connected_chunks_of_type(map_gen, chunk, 'town'))>=len(ROOM_TYPES):
			continue
		
		map_gen['chunk_map'][chunk]['type'] = 'town'
		
		_actual_town_chunks.append(chunk)
		
		if len(_actual_town_chunks)>_max_size:
			break
	
	for chunk_key in _actual_town_chunks[:]:
		_added = True
		_break = False
		while _added:
			_added = False
			
			for neighbor_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'other'):
				#if neighbor_key in _actual_town_chunks:
				#	continue
				
				if len(get_all_connected_chunks_of_type(map_gen, chunk_key, 'town'))>=len(ROOM_TYPES):
					_break = True
					break
				
				_skip = False
				for _next_neighbor in get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor_key]['pos'], 'town'):
					if not _next_neighbor in _actual_town_chunks:
						_skip = True
						break
				
				if _skip:
					continue
				
				if get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor_key]['pos'], 'road'):
					continue
				
				if random.randint(0, 3):
					continue
				
				_actual_town_chunks.append(neighbor_key)
				map_gen['chunk_map'][neighbor_key]['type'] = 'town'
				_added = True
		
			if _break:
				break
		
		if _break:
			break
	
	_covered_houses = []
	for chunk in _actual_town_chunks:
		#if not get_neighbors_of_type(map_gen, map_gen['chunk_map'][_driveways[chunk]]['pos'], 'driveway') and :
		if chunk in _covered_houses:
			continue
		
		_chunk = map_gen['chunk_map'][_driveways[chunk]]
		create_road(map_gen, _driveways[chunk], ground_tiles=tiles.CONCRETE_FLOOR_TILES, size=1)
		_chunk['type'] = 'driveway'
		
		_covered_houses.extend(get_all_connected_chunks_of_type(map_gen, _driveways[chunk], 'town'))
	
	_name = language.generate_place_name()
	
	map_gen['refs']['towns'][_name] = {'chunks': _actual_town_chunks}

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
				create_tile(map_gen, x, y, 2+z, random.choice(tiles.GRASS_TILES))

def create_tree(map_gen, position, height):
	_trunk = random.choice(tiles.TREE_STUMPS)
	
	for z in range(0, height):
		if z == height-1:
			_size = random.randint(4, 7)
			for pos in drawing.draw_circle(position[:2], _size):
				if pos[0]<0 or pos[0]>=map_gen['size'][0]-1 or pos[1]<0 or pos[1]>=map_gen['size'][1]-1:
					continue
					
				_dist = _size-numbers.clip(numbers.distance(position, pos), 1, height-map_gen['size'][2])
				for _z in range(_dist/2, _dist):
					if map_gen['map'][pos[0]][pos[1]][2+_z]:
						continue
					
					create_tile(map_gen, pos[0], pos[1], 2+_z, random.choice(tiles.LEAF_TILES))
		else:
			create_tile(map_gen, position[0], position[1], position[2]+z, _trunk)

def place_forest(map_gen):
	SMALLEST_FOREST = (80, 80)
	
	while 1:
		_top_left = (random.randint(0, numbers.clip(map_gen['size'][0]-SMALLEST_FOREST[0], SMALLEST_FOREST[0], map_gen['size'][0]-SMALLEST_FOREST[0])),
			         random.randint(0, map_gen['size'][1]-SMALLEST_FOREST[1]))
		
		if not (_top_left[0]+SMALLEST_FOREST[0])-(_top_left[0]+(map_gen['size'][0]-_top_left[0])) or\
		   not (_top_left[1]+SMALLEST_FOREST[1])-(_top_left[1]+(map_gen['size'][1]-_top_left[1])):
			continue
		
		_bot_right = (random.randint(_top_left[0]+SMALLEST_FOREST[0], _top_left[0]+(map_gen['size'][0]-_top_left[0])),
			          random.randint(_top_left[1]+SMALLEST_FOREST[1], _top_left[1]+(map_gen['size'][1]-_top_left[1])))
		
		break
	
	_size = (map_gen['size'][0], map_gen['size'][1], 5)
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
			if random.randint(0, _height*18):
				continue
			
			_actual_height = numbers.clip(_height, 2, 100)+(random.randint(2, 4))
			create_tree(map_gen, (x, y, 2), _actual_height)

def get_neighbors_of_type(map_gen, pos, chunk_type, diagonal=False, return_keys=True):
	_directions = [(0, -1), (-1, 0), (1, 0), (0, 1)]
	_keys = []
	_neighbors = 0
	
	if 'size' in map_gen:
		_size = map_gen['size']
	else:
		_size = MAP_SIZE
	
	if diagonal:
		_directions.extend([(-1, -1), (1, 1), (-1, 1), (1, 1)])
	
	for _dir in _directions:
		_next_pos = [pos[0]+(_dir[0]*map_gen['chunk_size']), pos[1]+(_dir[1]*map_gen['chunk_size'])]
		_next_key = '%s,%s' % (_next_pos[0], _next_pos[1])
		
		if _next_pos[0]<0 or _next_pos[0]>=_size[0] or _next_pos[1]<0 or _next_pos[1]>=_size[1]:
			continue
		
		if chunk_type == 'any' or map_gen['chunk_map'][_next_key]['type'] == chunk_type:
			_keys.append(_next_key)
			_neighbors += 1
	
	if return_keys:
		return _keys
	
	return _neighbors

def get_all_connected_chunks_of_type(map_gen, chunk_key, chunk_type):
	_connected_chunks = [chunk_key]
	_to_check = [chunk_key]
	
	while _to_check:
		_chunk_key = _to_check.pop(0)
		
		for neighbor in get_neighbors_of_type(map_gen, map_gen['chunk_map'][_chunk_key]['pos'], chunk_type):
			if neighbor in _connected_chunks:
				continue
			
			_to_check.append(neighbor)
			_connected_chunks.append(neighbor)
	
	return _connected_chunks

def walker(map_gen, pos, moves, brush_size=1, allow_diagonal_moves=True, avoid_chunks=[], avoid_chunk_distance=0):
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
			
			if avoid_chunks and alife.chunks.get_distance_to_nearest_chunk_in_list(_next_pos, avoid_chunks) < avoid_chunk_distance:
				continue
			
			_possible_dirs.append(_next_pos)
			
		if not _possible_dirs:
			return _walked
		
		_chosen_dir = random.choice(_possible_dirs)
		if _chosen_dir == _last_dir['dir']:
			_last_dir['times'] += 1
		else:
			_last_dir['dir'] = _chosen_dir[:]
			_last_dir['times'] += 1
		
		_pos[0] = _chosen_dir[0]
		_pos[1] = _chosen_dir[1]
		
		for _y in range(-brush_size, brush_size+1):
			for _x in range(-brush_size, brush_size+1):
				__x = _pos[0]+_x*map_gen['chunk_size']
				__y = _pos[1]+_y*map_gen['chunk_size']
				
				if __x < 0 or __x>=map_gen['size'][0] or __y < 0 or __y>=map_gen['size'][1]:
					continue
					
				_walked.append([__x, __y])
	
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

def clean_chunk_map(map_gen, chunk_type, minimum_chunks=2, chunks_of_type=None, replace_with_type='other', diagonal=False):
	_chunks = []
	if not chunks_of_type:
		chunks_of_type = chunk_type
	for y in range(0, map_gen['size'][1], map_gen['chunk_size']):
		for x in range(0, map_gen['size'][0], map_gen['chunk_size']):
			_chunk = map_gen['chunk_map']['%s,%s' % (x, y)]
			
			if not _chunk['type'] == chunk_type:
				continue
			
			if len(get_neighbors_of_type(map_gen, _chunk['pos'], chunks_of_type, diagonal=diagonal)) < minimum_chunks:
				_chunk['type'] = replace_with_type
				_chunks.append('%s,%s' % (x, y))
				    
	return _chunks

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

def create_road(map_gen, chunk_key, ground_tiles=tiles.CONCRETE_TILES, chunk_type='road', size=0, height=1):
	chunk = map_gen['chunk_map'][chunk_key]
	_directions = []
	
	for neighbor_key in get_neighbors_of_type(map_gen, chunk['pos'], chunk_type):
		_directions.append(direction_from_key_to_key(map_gen, chunk_key, neighbor_key))
	
	#for _direction in _directions:
	if len(_directions) == 1 and (0, -1) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(0, map_gen['chunk_size']):
				if y == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
				
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 1 and (0, 1) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(0, map_gen['chunk_size']):
				if y == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 1 and (1, 0) in _directions:
		for x in range(0, map_gen['chunk_size']):
			for y in range(size, map_gen['chunk_size']-size):
				if x == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 1 and (-1, 0) in _directions:
		for x in range(0, map_gen['chunk_size']):
			for y in range(size, map_gen['chunk_size']-size):
				if x == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
					
	elif len(_directions) == 2 and (-1, 0) in _directions and (1, 0) in _directions:
		for x in range(0, map_gen['chunk_size']):
			for y in range(size, map_gen['chunk_size']-size):
				if (y == 0 or y == map_gen['chunk_size']-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				elif y == round(map_gen['chunk_size']/2) and x % 3 and ground_tiles == tiles.CONCRETE_TILES:
					_tile = tiles.ROAD_STRIPE_2
					_height = height
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 2 and (0, -1) in _directions and (0, 1) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(0, map_gen['chunk_size']):
				if (x == 0 or x == map_gen['chunk_size']-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 2 and (0, -1) in _directions and (-1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if (y == map_gen['chunk_size']-1 or x == map_gen['chunk_size']-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 3 and (0, -1) in _directions and (-1, 0) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if y == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 3 and (0, 1) in _directions and (-1, 0) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if y == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 3 and (0, -1) in _directions and (0, 1) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if x == 0 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 3 and (0, -1) in _directions and (0, 1) in _directions and (-1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if x == map_gen['chunk_size']-1 and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 4:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				_tile = random.choice(ground_tiles)
				
				create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2, _tile)
	
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
		
		_wall_tile = tiles.WALL_TILE
		_floor_tiles = tiles.CONCRETE_FLOOR_TILES
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
							create_tile(map_gen, x, y, 2+i, _wall_tile)
						elif (not i or i == 2) and _building[_y][_x] == '.':
							create_tile(map_gen, x, y, 2+i, random.choice(_floor_tiles))
							
							if not i and random.randint(0, 500) == 500:
								effects.create_light((x, y, 2), (255, 0, 255), 5, 0.1)

def construct_town(map_gen, town):
	#_houses = []
	_taken = []
	for chunk_key in town:
		if chunk_key in _taken:
			continue
		
		#_chunk = map_gen['chunk_map'][chunk_key]
		_house = [chunk_key]
		_house_dirs = {}
		_to_check = [chunk_key]
		while _to_check:
			_checking_chunk_key = _to_check.pop(0)
			_chunk = map_gen['chunk_map'][_checking_chunk_key]
			_neighbors = get_neighbors_of_type(map_gen, _chunk['pos'], 'town')
			_added = False
			for neighbor_key in _neighbors:
				if not neighbor_key in _house:
					_house.append(neighbor_key)
					_to_check.append(neighbor_key)
					_added = True
			
			if not _added:
				break
		
		#_houses.append(_house)
		_taken.extend(_house)
		
		_main_rooms = ['bedroom', 'bathroom']
		_secondary_rooms = ['kitchen', 'dining room']
		_wall_tile = random.choice(tiles.HOUSE_WALL_TILES)
		
		for chunk_key in _house[:]:
			if 'room_type' in map_gen['chunk_map'][chunk_key]['flags']:
				_room_type = map_gen['chunk_map'][chunk_key]['flags']['room_type']
			elif _main_rooms:
				_room_type = _main_rooms.pop(random.randint(0, len(_main_rooms)-1))
			elif _secondary_rooms:
				_room_type = _secondary_rooms.pop(random.randint(0, len(_secondary_rooms)-1))
			else:
				print 'pass due to empty room list'
				map_gen['chunk_map'][chunk_key]['type'] = 'other'
				_last_placed_index = _house.index(chunk_key)
				_house.remove(chunk_key)
				
				for delete_key in _house[_last_placed_index:]:
					map_gen['chunk_map'][delete_key]['type'] = 'other'
					print 'cleaned'
				
				break
			
			_items = []
			_storage = []
			if _room_type == 'bedroom':
				_floor_tiles = tiles.DARK_GREEN_FLOOR_TILES
				_items = [{'item': 'blue jeans', 'rarity': 1.0},
				               {'item': 'leather backpack', 'rarity': 0.65},
				               {'item': 'sneakers', 'rarity': 1.0},
				               {'item': 'white t-shirt', 'rarity': 1.0},
				               {'item': 'white cloth', 'rarity': 0.4}]
				_storage = [{'item': 'wooden dresser', 'rarity': 1.0, 'spawn_list': _items}]
			elif _room_type == 'bathroom':
				_floor_tiles = tiles.BLUE_FLOOR_TILES
				_items = [{'item': 'blue jeans', 'rarity': 1.0},
				               {'item': 'leather backpack', 'rarity': 0.65},
				               {'item': 'sneakers', 'rarity': 1.0},
				               {'item': 'white t-shirt', 'rarity': 1.0},
				               {'item': 'white cloth', 'rarity': 0.4}]
			elif _room_type == 'kitchen':
				_floor_tiles = tiles.BROWN_FLOOR_TILES
			
			_avoid_directions = []
			_directions = []
			_chunk = map_gen['chunk_map'][chunk_key]
			for neighbor_key in get_neighbors_of_type(map_gen, _chunk['pos'], 'any'):
				if not neighbor_key in _house and not map_gen['chunk_map'][neighbor_key]['type'] == 'driveway':
					_avoid_directions.append(DIRECTION_MAP[str(direction_from_key_to_key(map_gen, chunk_key, neighbor_key))])
					continue
				
				if map_gen['chunk_map'][neighbor_key]['type'] in ['town', 'driveway']:
					_directions.append(DIRECTION_MAP[str(direction_from_key_to_key(map_gen, chunk_key, neighbor_key))])
				
				#_neighbor_chunk = map_gen['chunk_map'][neighbor_key]
				#for next_neighbor_key in get_neighbors_of_type(map_gen, _neighbor_chunk['pos'], 'driveway'):
				#	_dir = DIRECTION_MAP[str(direction_from_key_to_key(map_gen, neighbor_key, next_neighbor_key))]
				#	
				#	#if _dir in _directions:
				#	#	continue
				#	
				#	_directions.append(_dir)
				#	print 'yeah'
		
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
			
			_neighbor_dirs = [DIRECTION_MAP[str(d)] for d in [direction_from_key_to_key(map_gen, chunk_key, n) for n in get_neighbors_of_type(map_gen, _chunk['pos'], 'town')]]
			_building = random.choice(_possible_tiles)
			_half = map_gen['chunk_size']/2
			
			_open_spots = []
			for _y in range(map_gen['chunk_size']):
				y = _chunk['pos'][1]+_y
				for _x in range(map_gen['chunk_size']):
					x = _chunk['pos'][0]+_x
					
					for i in range(3):
						if i == 2:#000000000000000000000000000000000000000000000000000000000000000000000000000000:
							map_gen['map'][x][y][2+i] = tiles.create_tile(_wall_tile)
							#h_x = _half-(abs(_half-_x))
							#h_y = _half-(abs(_half-_y))
							
							##if len(_neighbor_dirs) == 1 and 'right' in _neighbor_dirs:
							#if not _neighbor_dirs:
								#if _x < _half:
									#map_gen['map'][x][y][2+i+h_x] = tiles.create_tile(map_gen, tiles.ROOF_DARK)
								#else:
									#map_gen['map'][x][y][2+i+h_x] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
							#elif len(_neighbor_dirs) == 1 and 'right' in _neighbor_dirs:
								#if _x<_half and ((_y<_half and _y >= h_x) or (_y>=_half-1 and _y <= (_half+h_y)+1)):
									#map_gen['map'][x][y][2+i+h_x] = tiles.create_tile(map_gen, tiles.ROOF_DARK)
								
								#elif _y < h_x and _y < _half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
								
								#elif _y >= h_x and _y < _half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
								
								#elif _y > _half and _y > map_gen['chunk_size']-(_half+h_x):
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_DARKER)
								
								#elif _y > _half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_DARKER)
			
								#else:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
							
							#elif len(_neighbor_dirs) == 1 and 'left' in _neighbor_dirs:
								#if _x>_half and ((_y<_half and _y >= h_x) or (_y>=_half-1 and _y <= (_half+h_y)+1)):
									#map_gen['map'][x][y][2+i+h_x] = tiles.create_tile(map_gen, tiles.ROOF_DARK)
								
								#elif _y < h_x and _y < _half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
								
								#elif _y >= h_x and _y < _half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
								
								#elif _y > _half and _y > map_gen['chunk_size']-(_half+h_x):
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_DARKER)
								
								#elif _y > _half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_DARKER)
			
								#else:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
	
							#elif len(_neighbor_dirs) == 2 and 'left' in _neighbor_dirs and 'right' in _neighbor_dirs:
								#if _y<=_half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
								
								#else:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_DARKER)
							
							#elif len(_neighbor_dirs) == 3 and 'left' in _neighbor_dirs and 'right' in _neighbor_dirs and 'bot' in _neighbor_dirs:
								#if _y<=_half:
									#map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)
								
								#else:#elif _x<_half and ((_y<_half and _y > h_x) or (_y>=_half-1 and _y <= (_half+h_y)+1)):
									#map_gen['map'][x][y][2+i+(h_x)] = tiles.create_tile(map_gen, tiles.ROOF_DARK)
								
								##else:
								##	map_gen['map'][x][y][2+i+h_y] = tiles.create_tile(map_gen, tiles.ROOF_DARKER)
							#elif len(_neighbor_dirs) == 4:
								#map_gen['map'][x][y][2+i] = tiles.create_tile(map_gen, tiles.ROOF_BRIGHT)

						elif _building[_y][_x] == '#':
							create_tile(map_gen, x, y, 2+i, _wall_tile)
						elif i in [0] and _building[_y][_x] == '.':
							create_tile(map_gen, x, y, 2+i, random.choice(_floor_tiles))
							
							if not i and random.randint(0, 500) == 500:
								effects.create_light((x, y, 2), (255, 0, 255), 5, 0.1)
							
							_open_spots.append((x, y))
			
			_possible_spots = []
			for pos in _open_spots:
				_open = 0
				for _n_pos in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
					if (pos[0]+_n_pos[0], pos[1]+_n_pos[1]) in _open_spots:
						_open += 1
				
				_possible_spots.append({'spot': pos[:], 'open_neighbors': _open})
			
			_only_one_neighbor = []
			for entry in _possible_spots:
				if entry['open_neighbors'] == 3:
					_only_one_neighbor.append(entry)
			
			if not _only_one_neighbor:
				continue
			
			_spawn_x, _spawn_y = random.choice([s['spot'] for s in _only_one_neighbor])
			_placed_containers = []
			if _storage:
				for _container in _storage:
					if not _container['rarity']>random.uniform(0, 1.0):
						continue
					
					_c = items.create_item(_container['item'], position=[_spawn_x, _spawn_y, 2])
					_placed_containers.append(_container)
					
					for _inside_item in _container['spawn_list']:
						if not can_spawn_item(_inside_item):
							continue
						
						_i = items.create_item(_inside_item['item'], position=[_spawn_x, _spawn_y, 2])
						
						if not items.can_store_item_in(_i, _c):
							items.delete_item(_i)
							continue
						
						items.store_item_in(_i, _c)
						
			elif _items:
				pass
			
			for container in _placed_containers:
				_storage.remove(container)

def can_spawn_item(item):
	if item['rarity']>random.uniform(0, 1.0):
		return True
	
	return False

def fill_empty_spaces(map_gen, fields=3):
	_empty_spots = []
	_field_spawns = []
	_fields = {}
	
	#for y in range(0, map_gen['map_size'][1]/map_gen['chunk_size'], map_gen['chunk_size']):
	#	for x in range(0, map_gen['map_size'][0]/map_gen['chunk_size'], map_gen['chunk_size']):
	#		if 
	for chunk_key in map_gen['chunk_map']:
		_chunk = map_gen['chunk_map'][chunk_key]
		
		if not _chunk['type'] == 'other':
			continue
		
		_empty_spots.append(chunk_key)
	
	for i in range(fields):
		_spots = _empty_spots[:]
		
		while _spots:
			_spot = _spots.pop(random.randint(0, len(_spots)-1))
			_chunk = map_gen['chunk_map'][_spot]
			
			#logging.info(len(get_neighbors_of_type(map_gen, _chunk['pos'], 'other', diagonal=True, return_keys=True)))
			if len(get_neighbors_of_type(map_gen, _chunk['pos'], 'other', diagonal=True)) < 8:
				continue
			
			logging.info('here')
			
			if _field_spawns:
				if alife.chunks.get_distance_to_nearest_chunk_in_list(_chunk['pos'], _field_spawns) < FIELD_DISTANCE:
					continue
			
			_field_spawns.append(_spot[:])
			break
	
	_placed_field_chunks = []
	for _field in _field_spawns:
		_start_chunk = map_gen['chunk_map'][_field]
		#avoid_chunks=['%s,%s' % (x,y) for x,y in _placed_field_chunks]
		_placed_field_chunks.extend(walker(map_gen, _start_chunk['pos'], random.randint(FIELD_SIZE_RANGE[0], FIELD_SIZE_RANGE[1])*map_gen['chunk_size']))
	
	for _chunk_key in ['%s,%s' % (x, y) for x,y  in _placed_field_chunks]:
		map_gen['chunk_map'][_chunk_key]['type'] = 'wash'

def decorate_world(map_gen):
	#backyards
	for town in map_gen['refs']['towns']:
		if not map_gen['settings']['back yards']:
			break
		
		_backyard = []
		for chunk_key in town:
			_chunk = map_gen['chunk_map'][chunk_key]
			for neighbor in get_neighbors_of_type(map_gen, _chunk['pos'], 'other', diagonal=True):
				if not get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor]['pos'], 'driveway', diagonal=False):
					_backyard.append(neighbor)
		
		for chunk_key in _backyard:
			_chunk = map_gen['chunk_map'][chunk_key]
			_chunk['type'] = 'backyard'
			_pos = (_chunk['pos'][0]+random.randint(0, map_gen['chunk_size']-1),
			        _chunk['pos'][1]+random.randint(0, map_gen['chunk_size']-1), 2)
			
			#create_tree(map_gen, _pos, random.randint(4, 7))
	
	#fences
	_possible_fences = []
	_low_end = random.randint(0, 5)
	_fences = 5+random.randint(3, 6)
	for chunk_key in map_gen['refs']['roads']:
		for neighbor in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'other'):
			_fences -= 1
			
			if not get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor]['pos'], 'driveway'):
				continue
			
			if not _fences:
				_fences = 5+random.randint(3, 6)
			elif _fences<=_low_end:
				map_gen['chunk_map'][neighbor]['type'] = 'wfence'
				_possible_fences.append(neighbor)
	
	for fence in _possible_fences:
		create_road(map_gen, fence, size=2, height=3, chunk_type='driveway', ground_tiles=tiles.WOOD_TILES)

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
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	console_formatter = logging.Formatter('[%(asctime)s-%(levelname)s] %(message)s',datefmt='%H:%M:%S %m/%d/%y')
	ch = logging.StreamHandler()
	ch.setFormatter(console_formatter)
	logger.addHandler(ch)
	
	tiles.create_all_tiles()
	items.initiate_all_items()
	language.load_strings()

	_t = time.time()
	if '--profile' in sys.argv:
		cProfile.run('generate_map(skip_zoning=False)','mapgen_profile.dat')
	else:
		generate_map(size=(200, 200, 10), towns=2, factories=0, forests=1, skip_zoning=(not '--zone' in sys.argv), skip_chunking=(not '--chunk' in sys.argv))
	
	print 'Total mapgen time:', time.time()-_t