from globals import *

import libtcodpy as tcod

import render_los
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

MAX_WAREHOUSE_SIZE = 16
MAX_TOWNHOUSE_SIZE = 8
MAX_BUILDING_SIZE = max([MAX_TOWNHOUSE_SIZE, MAX_WAREHOUSE_SIZE])
TOWN_DISTANCE = 60*5
TOWN_SIZE = 160
FOREST_DISTANCE = 10
OUTPOST_DISTANCE = 12*5
OPEN_TILES = ['.']
DOOR_TILES = ['D']
DIRECTION_MAP = {'(-1, 0)': 'left', '(1, 0)': 'right', '(0, -1)': 'top', '(0, 1)': 'bot'}
ROOM_TYPES = {'bedroom': {'required': True, 'floor_tiles': tiles.DARK_GREEN_FLOOR_TILES},
              'bathroom': {'required': True, 'floor_tiles': tiles.BLUE_FLOOR_TILES},
              'kitchen': {'floor_tiles': tiles.BROWN_FLOOR_TILES},
              'dining_room': {'floor_tiles': tiles.WHITE_TILE_TILES}}
BUSH_EXCLUDE_TILES = [t['id'] for t in tiles.GRASS_TILES]
BUSH_EXCLUDE_TILES.extend([t['id'] for t in tiles.DIRT_TILES])
BUILDING_EXCLUDE_TILES = [t['id'] for t in tiles.GRASS_TILES]
BUILDING_EXCLUDE_TILES.extend([t['id'] for t in tiles.BUSH_TILES])
BUILDING_EXCLUDE_TILES.extend([t['id'] for t in tiles.DIRT_TILES])


def create_building(buildings, building, chunk_size):
	_top = False
	_bot = False
	_left = False
	_right = False
	_door_top = False
	_door_bot = False
	_door_left = False
	_door_right = False
	
	for y in range(chunk_size):
		for x in range(chunk_size):
			_tile = building[y][x]
			
			if x == 0 and (y>0 or y<chunk_size) and _tile in OPEN_TILES:
				_left = True
			elif x == 0 and (y>0 or y<chunk_size) and _tile in DOOR_TILES:
				_door_left = True
			
			if x == chunk_size-1 and (y>0 or y<chunk_size) and _tile in OPEN_TILES:
				_right = True
			elif x == chunk_size-1 and (y>0 or y<chunk_size) and _tile in DOOR_TILES:
				_door_right = True
			
			if y == 0 and (x>0 or x<chunk_size) and _tile in OPEN_TILES:
				_top = True
			elif y == 0 and (x>0 or x<chunk_size) and _tile in DOOR_TILES:
				_door_top = True
			
			if y == chunk_size-1 and (x>0 or x<chunk_size) and _tile in OPEN_TILES:
				_bot = True
			elif y == chunk_size-1 and (x>0 or x<chunk_size) and _tile in DOOR_TILES:
				_door_bot = True
	
	_building_temp = {'open': {'top': _top, 'bot': _bot, 'left': _left, 'right': _right},
	                  'door': {'top': _door_top, 'bot': _door_bot, 'left': _door_left, 'right': _door_right},
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

def create_tile(map_gen, x, y, z, tile):
	map_gen['map'][x][y][z] = tiles.create_tile(tile)
	
	_raw_tile = tiles.get_raw_tile(map_gen['map'][x][y][z])
	if 'not_solid' in _raw_tile and _raw_tile['not_solid']:
		return True
	
	_chunk = map_gen['chunk_map'][alife.chunks.get_chunk_key_at((x, y))]
	if z > _chunk['max_z']:
		_chunk['max_z'] = z

def generate_map(size=(450, 450, 10), detail=5, towns=2, factories=1, forests=1, outposts=3, underground=True, skip_zoning=False, skip_chunking=False, hotload=False):
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
		'noise_view_size': 100.0,
		'noise_zoom': 3.5,
		'town_fuzz': 45.0,#50.0,
		'road_fuzz': 15.5,
		'towns': towns,
		'factories': factories,
		'forests': forests,
		'outposts': outposts,
		'underground': underground,
		'chunk_map': {},
		'refs': {'factories': [], 'villages': [], 'towns': [], 'forests': [], 'roads': [], 'town_seeds': [], 'outposts': [], 'dirt_road': []},
		'buildings': load_tiles('buildings.txt', detail),
		'flags': {},
		'map': maps.create_map(size=size),
		'queued_roads': [],
		'settings': {'back yards': True, 'town size': (20, 25)}}
	
	_map_size = maputils.get_map_size(map_gen['map'])
	MAP_SIZE[0] = _map_size[0]
	MAP_SIZE[1] = _map_size[1]
	MAP_SIZE[2] = _map_size[2]
	
	WORLD_INFO['chunk_map'] = map_gen['chunk_map']
	
	#logging.debug('Creating height map...')
	#generate_height_map(map_gen)
	logging.debug('Creating chunk map...')
	generate_chunk_map(map_gen)
	logging.debug('Drawing outlines...')
	#generate_outlines(map_gen)
	
	generate_noise_map(map_gen)
	
	logging.debug('Creating roads...')
	for chunk_key in map_gen['refs']['roads']:
		create_road(map_gen, chunk_key)
	
	#logging.debug('Building factories...')
	#for _factory in map_gen['refs']['factories']:
		#construct_factory(map_gen, _factory)
	
	logging.debug('Building villages...')
	for village in map_gen['refs']['villages']:
		construct_village(map_gen, village)
	
	logging.debug('Building towns...')
	for town in map_gen['refs']['towns']:
		construct_town(map_gen, town)
	
	logging.debug('Generating outposts...')	
	#for i in range(map_gen['outposts']):
	#	construct_outpost(map_gen)	
	
	map_gen['refs']['roads'].extend(map_gen['refs']['dirt_road'])
	
	#Placeholder!
	logging.debug('Placing region spawns...')
	create_region_spawns()
	
	logging.debug('Occupying empty spaces...')
	fill_empty_spaces(map_gen)
	
	logging.debug('Decorating world...')
	decorate_world(map_gen)
	
	logging.debug('Rounding off edges...')
	round_off_edges(map_gen)
	
	logging.debug('Placing forests...')
	#while len(map_gen['refs']['forests'])<map_gen['forests']:
	#	map_gen['refs']['forests'].append(place_forest(map_gen))
	
	##place_hills(map_gen)
	##print_map_to_console(map_gen)
	
	#clean_chunk_map(map_gen, 'driveway', chunks_of_type='town', minimum_chunks=1)
	clean_chunk_map(map_gen, 'wall', chunks_of_type='wall', minimum_chunks=1)
	
	#if not hotload:
	#	print_chunk_map_to_console(map_gen)
	
	map_gen['items'] = ITEMS
	WORLD_INFO.update(map_gen)
	
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
	
	if not skip_chunking and not skip_chunking:
		items.save_all_items()
		
		if not hotload:
			maps.save_map(map_gen['name'])
		
		items.reload_all_items()
	
	logging.debug('Map generation complete.')	
	
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
				'flags': {},
				'type': 'other',
				'max_z': 2}

def generate_noise_map(map_gen):
	_cells = []
	_size = (map_gen['size'][0], map_gen['size'][1])
	_noise_map = numpy.zeros(_size[:2])
	_noise = tcod.noise_new(4)
	_noise_dx = 0
	_noise_dy = 0
	_noise_octaves = 3.0
	_town_seeds = []
	_trees = []
	_bushes = []
	
	for y in range(0, _size[1], map_gen['chunk_size']):
		for x in range(0, _size[0], map_gen['chunk_size']):
			_chunk_key = '%s,%s' % (x, y)
			_noise_values = [map_gen['noise_zoom'] * x / (2*map_gen['noise_view_size']) + _noise_dx,
			          map_gen['noise_zoom'] * y / (2*map_gen['noise_view_size']) + _noise_dy]
			_value = abs(tcod.noise_get(_noise, _noise_values, tcod.NOISE_SIMPLEX)/4.0)
			_r = 255*_value
			_g = 255*_value
			_b = 255*_value
			
			_val = _r+_g+_b
			
			if _val <= map_gen['road_fuzz']:
				_fuzz_val = _val/map_gen['road_fuzz']
				
				for pos in drawing.draw_circle((x, y), random.randint(6, 8)):
					if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
						continue
					
					create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.DIRT_TILES))
					
					if _fuzz_val < .1:
						create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.BROKEN_CONCRETE_FLOOR_TILES))
					elif _fuzz_val < .65:
						create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.CONCRETE_TILES))
					elif _fuzz_val < .7:
						#if random.randint(0, 4):
						create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.CONCRETE_TILES))
						#else:
						#	create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.BROKEN_CONCRETE_FLOOR_TILES))
					elif _fuzz_val < .8 and random.randint(0, 7):
						create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.BROKEN_CONCRETE_TILES))
					elif not random.randint(0, 6):
						create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.BROKEN_CONCRETE_TILES))
				
				if not _chunk_key in map_gen['refs']['dirt_road']:
					map_gen['refs']['dirt_road'].append(_chunk_key)
					map_gen['chunk_map'][_chunk_key]['type'] = 'road'
				
			elif _val >= map_gen['town_fuzz']:
				if not _chunk_key in _town_seeds:
					_town_seeds.append(_chunk_key)
				
			elif map_gen['road_fuzz'] < _val < map_gen['town_fuzz']:
				#if not _chunk_key in map_gen['refs']['forests']:
				#	map_gen['refs']['forests'].append(_chunk_key)
				_chance = random.uniform(0, 1)
				if _chance<.9:
					_x = numbers.clip(x+random.randint(0, 5), 0, MAP_SIZE[0]-1)
					_y = numbers.clip(y+random.randint(0, 5), 0, MAP_SIZE[1]-1)
					
					if not map_gen['map'][_x][_y][2]['id'] in [t['id'] for t in tiles.GRASS_TILES]:
						continue
					
					_trees.append((_x, _y, 2, random.randint(4, 7)))
					
					map_gen['chunk_map'][_chunk_key]['type'] = 'forest'
				
				if _chance<.8:
					for pos in drawing.draw_circle((x, y), random.randint(6, 8)):
						if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
							continue
						
						_x = numbers.clip(pos[0]+random.randint(0, 5), 0, MAP_SIZE[0]-1)
						_y = numbers.clip(pos[1]+random.randint(0, 5), 0, MAP_SIZE[1]-1)
						
						if not map_gen['map'][_x][_y][2]['id'] in BUSH_EXCLUDE_TILES:
							continue
						
						_bushes.append((_x, _y, 2))
					
					map_gen['chunk_map'][_chunk_key]['type'] = 'forest'
	
	for tree in _trees:
		if not map_gen['map'][tree[0]][tree[1]][tree[2]]['id'] in [t['id'] for t in tiles.GRASS_TILES]:
			continue
		
		create_tree(map_gen, tree[:3], tree[3])
	
	for bush in _bushes:
		if not map_gen['map'][bush[0]][bush[1]][bush[2]]['id'] in BUSH_EXCLUDE_TILES:
			continue
		
		create_tile(map_gen, bush[0], bush[1], bush[2], random.choice(tiles.BUSH_TILES))

	#Find all cells
	while _town_seeds:
		_chunk_key = _town_seeds.pop()
		_top_left = MAP_SIZE[:]
		_bot_right = [0, 0, 0]
		_connected_chunk_keys = get_all_connected_chunks_of_type(map_gen, _chunk_key, 'other')
		
		for chunk_key in _connected_chunk_keys:
			if chunk_key in _town_seeds:
				_town_seeds.remove(chunk_key)
			
			_chunk_pos = map_gen['chunk_map'][chunk_key]['pos']
			
			if _chunk_pos[0]<_top_left[0]:
				_top_left[0] = _chunk_pos[0]
			
			if _chunk_pos[0]>_bot_right[0]:
				_bot_right[0] = _chunk_pos[0]
			
			if _chunk_pos[1]<_top_left[1]:
				_top_left[1] = _chunk_pos[1]
			
			if _chunk_pos[1]>_bot_right[1]:
				_bot_right[1] = _chunk_pos[1]
		
		_center_pos = numbers.lerp_velocity(_top_left, _bot_right, 0.5)[:2]
		_center_pos[0] = int(_center_pos[0])
		_center_pos[1] = int(_center_pos[1])
		_cells.append({'size': len(_connected_chunk_keys),
		               'type': None,
		               'chunk_keys': _connected_chunk_keys,
		               'top_left': _top_left,
		               'bot_right': _bot_right,
		               'center_pos': _center_pos[:]})
	
	_cell_types = {'Outpost': {'callback': generate_outpost,
	                           'min_cells': 20,
	                           'max_cells': 70,
	                           'difficulty_min': 0.1,
	                           'difficulty_max': 0.75},
	               'Farm': {'callback': generate_farm,
	                           'min_cells': 200,
	                           'max_cells': 500,
	                           'difficulty_min': 0.0,
	                           'difficulty_max': 0.55}}
	_empty_cell_types = {'Forest': generate_forest}	
	_zone_entry_position = (125, 125)
	_npp_position = (map_gen['size'][0]-120, map_gen['size'][1]-120)
	_difficulty_distance = numbers.distance(_zone_entry_position, _npp_position)
	
	map_gen['zone_entry_chunk_key'] = '%s,%s' % (_zone_entry_position[0], _zone_entry_position[1])
	
	#Fields and farms
	for cell in _cells:
		
		#Find matching cell type
		for cell_type in _cell_types.values():
			_difficulty_percentage = numbers.clip(numbers.distance(cell['center_pos'], _zone_entry_position)/float(_difficulty_distance), 0, 1)
			print _difficulty_percentage, _difficulty_distance
			if not cell_type['difficulty_min'] < _difficulty_percentage <= cell_type['difficulty_max']:
				continue
			
			if cell_type['min_cells'] < cell['size'] <= cell_type['max_cells']:
				_matched = True
				cell_type['callback'](map_gen, cell)
				
				break
		else:
			_empty_cell_type = random.choice(_empty_cell_types.keys())
			_empty_cell_types[_empty_cell_type](map_gen, cell)
			
			logging.debug('Cell has no matching cell type, using \'%s\'.' % _empty_cell_type)

def generate_outpost(map_gen, cell):
	_center_chunk_key = alife.chunks.get_chunk_key_at(cell['center_pos'])
	_center_chunk = map_gen['chunk_map'][_center_chunk_key]
	_outpost_chunk_keys = walker(map_gen,
	                             _center_chunk['pos'],
	                             random.randint(10, 14),
	                             only_chunk_types=['other'],
	                             avoid_chunk_distance=4*map_gen['chunk_size'],
	                             return_keys=True)
	
	for chunk_key in _outpost_chunk_keys:
		map_gen['chunk_map'][chunk_key]['type'] = 'town'
	
	_exterior_chunk_keys = []
	for chunk_key in _outpost_chunk_keys:
		for neighbor_chunk_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'other'):
			if neighbor_chunk_key in _exterior_chunk_keys:
				continue
			
			_exterior_chunk_keys.append(neighbor_chunk_key)
	
	_exterior_chunk_key = random.choice(_exterior_chunk_keys)
	construct_building(map_gen, {'rooms': _outpost_chunk_keys}, exterior_chunks=[_exterior_chunk_key])

def generate_forest(map_gen, cell):
	for chunk_key in cell['chunk_keys']:
		_tiles_in_chunk = map_gen['chunk_size']**2
		map_gen['chunk_map'][chunk_key]['type'] = 'forest'
		
		for i in range(int(round(_tiles_in_chunk*.15)), int(round(_tiles_in_chunk*.25))):
			_x = map_gen['chunk_map'][chunk_key]['pos'][0]+random.randint(0, map_gen['chunk_size'])
			_y = map_gen['chunk_map'][chunk_key]['pos'][1]+random.randint(0, map_gen['chunk_size'])
			
			if _x<0 or _x>=MAP_SIZE[0] or _y<0 or _y>=MAP_SIZE[1]:
				continue
			
			if map_gen['map'][_x][_y][2]['id'] in [t['id'] for t in tiles.GRASS_TILES]:
				create_tree(map_gen, (_x, _y, 2), random.randint(3, 4))
				
				if random.randint(0, 4):
					create_bush(map_gen, (_x, _y, 2), random.randint(3, 6), dither=True)

def generate_farm(map_gen, cell):
	#Farmland (crops)
	_farmland_chunks = cell['chunk_keys'][:]
	for chunk_key in _farmland_chunks:
		_chunk_pos = map_gen['chunk_map'][chunk_key]['pos']
		
		for pos in drawing.draw_circle(_chunk_pos[:2], random.randint(6, 8)):
			if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
				continue
			
			if not map_gen['map'][pos[0]][pos[1]][2]['id'] in [t['id'] for t in tiles.GRASS_TILES]:
				continue
			
			create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.FIELD_TILES))
	
	#Farmhouse
	_chunk_key = random.choice(cell['chunk_keys'])
	_building_chunks = walker(map_gen,
                              map_gen['chunk_map'][_chunk_key]['pos'],
                              random.randint(5, 8),
                              avoid_chunks=map_gen['refs']['roads'],
                              only_chunk_types=['other'],
                              avoid_chunk_distance=5*map_gen['chunk_size'],
                              return_keys=True)
	
	_yard_chunks = []
	for chunk_key in _building_chunks:
		map_gen['chunk_map'][chunk_key]['type'] = 'town'
		
		if chunk_key in _farmland_chunks:
			_farmland_chunks.remove(chunk_key)
		
		for neighbor_chunk_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'other', diagonal=True):
			if neighbor_chunk_key in _building_chunks:
				continue
			
			if neighbor_chunk_key in _farmland_chunks:
				_farmland_chunks.remove(neighbor_chunk_key)
			
			_yard_chunks.append(neighbor_chunk_key)
			_center_pos = list(map_gen['chunk_map'][neighbor_chunk_key]['pos'][:2])
			_center_pos[0] += map_gen['chunk_size']/2
			_center_pos[1] += map_gen['chunk_size']/2
			
			for pos in drawing.draw_circle(_center_pos, random.randint(6, 8)):
				if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
					continue
				
				if not map_gen['map'][pos[0]][pos[1]][2]['id'] in [t['id'] for t in tiles.FIELD_TILES]:
					continue
				
				create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.GRASS_TILES))
	
	_exterior_chunk_keys = set()
	for chunk_key in _building_chunks:
		_exterior_chunk_keys.update(get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'other'))
	
	#Outlining the farmhouse
	_top_left = MAP_SIZE[:2]
	_bot_right = [0, 0]
	for chunk_key in _yard_chunks:
		_chunk = map_gen['chunk_map'][chunk_key]
		_chunk['type'] = 'yard'
		
		if _chunk['pos'][0] < _top_left[0]:
			_top_left[0] = _chunk['pos'][0]
		
		if _chunk['pos'][1] < _top_left[1]:
			_top_left[1] = _chunk['pos'][1]
		
		if _chunk['pos'][0] > _bot_right[0]:
			_bot_right[0] = _chunk['pos'][0]
		
		if _chunk['pos'][1] > _bot_right[1]:
			_bot_right[1] = _chunk['pos'][1]
	
	#Farmhouse fence
	for y in range(_top_left[1], _bot_right[1]+1):
		_y = y-_top_left[1]
		
		for x in range(_top_left[0], _bot_right[0]+1):
			_x = x-_top_left[0]
		
			if not _x or not _y or x == _bot_right[0] or y == _bot_right[1]:
				create_tile(map_gen, x+map_gen['chunk_size']/2, y+map_gen['chunk_size']/2, 2, random.choice(tiles.WOOD_TILES))
	
	construct_building(map_gen, {'rooms': _building_chunks}, exterior_chunks=[random.choice(list(_exterior_chunk_keys))])
	
	#Silos
	_potential_silo_chunks = []
	_min_farmhouse_distance = 4*map_gen['chunk_size']
	_max_farmhouse_distance = 8*map_gen['chunk_size']
	
	for chunk_key in _farmland_chunks:
		_potential_silo_chunk = map_gen['chunk_map'][chunk_key]
		
		_continue = False
		for farmhouse_chunk_key in _building_chunks:
			_farmhouse_chunk = map_gen['chunk_map'][farmhouse_chunk_key]
			_dist = numbers.distance(_potential_silo_chunk['pos'], _farmhouse_chunk['pos'])
			
			if not _min_farmhouse_distance < _dist <= _max_farmhouse_distance:
				_continue = True
				break
			
		if _continue:
			continue
			
		_potential_silo_chunks.append(chunk_key)
	
	if not _potential_silo_chunks:
		raise Exception('No room for farm silo.')
	
	_silo_chunk_key = random.choice(_potential_silo_chunks)
	_silo_chunk = map_gen['chunk_map'][_silo_chunk_key]
	_silo_chunk['type'] = 'silo'
	
	for y in range(_silo_chunk['pos'][1]-(map_gen['chunk_size'])-1, _silo_chunk['pos'][1]+(map_gen['chunk_size']*2)+1):
		for x in range(_silo_chunk['pos'][0]-(map_gen['chunk_size'])-1, _silo_chunk['pos'][0]+(map_gen['chunk_size']*2)+1):
			if x<0 or x>=MAP_SIZE[0] or y<0 or y>=MAP_SIZE[1]:
				continue
			
			if not map_gen['map'][x][y][2]['id'] in [t['id'] for t in tiles.FIELD_TILES]:
				if not random.randint(0, 4):
					create_tile(map_gen, x, y, 2, random.choice(tiles.BROKEN_CONCRETE_FLOOR_TILES))
				elif not random.randint(0, 4):
					create_tile(map_gen, x, y, 2, random.choice(tiles.CONCRETE_FLOOR_TILES))
			else:
				create_tile(map_gen, x, y, 2, random.choice(tiles.CONCRETE_FLOOR_TILES))
	
	_breaks = []
	_center = (_silo_chunk['pos'][0]+map_gen['chunk_size']/2, _silo_chunk['pos'][1]+map_gen['chunk_size']/2)
	for z in range(1, 4):
		for pos in drawing.draw_circle(_center, 10):
			if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
				continue
			
			if not map_gen['map'][pos[0]][pos[1]][2]['id'] in BUILDING_EXCLUDE_TILES:
				create_tile(map_gen, pos[0], pos[1], 2+z, random.choice(tiles.WHITE_TILE_TILES))
			else:
				_breaks.append({'pos': (pos[0], pos[1], 2+z),
			                    'distance': numbers.distance(_center, pos),
			                    'direction': numbers.direction_to(_center, pos)})
	
	for break_pos in _breaks:
		_velocity = numbers.velocity(break_pos['direction'], numbers.clip(break_pos['distance']/5, 0.5, 1))
		_velocity[0] = break_pos['pos'][0]+_velocity[0]
		_velocity[1] = break_pos['pos'][1]+_velocity[1]
		
		for z in range(1, break_pos['pos'][2]):
			_i = z/numbers.clip(z/float(MAP_SIZE[2]), 0, 5)

			_center_pos = numbers.lerp_velocity(break_pos['pos'], _velocity, _i)
			_center_pos = (int(round(_center_pos[0])), int(round(_center_pos[1])))
			for pos in drawing.draw_circle(_center_pos, 4):
				if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
					continue
				
				if map_gen['map'][pos[0]][pos[1]][2]['id'] in [t['id'] for t in tiles.TREE_STUMPS]:
					continue
				
				if not random.randint(0, 3):
					create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.WHITE_TILE_TILES))
				else:
					create_tile(map_gen, pos[0], pos[1], 2, random.choice(tiles.GRASS_TILES))

def generate_outlines(map_gen):
	logging.debug('Placing roads and towns...')
	place_road(map_gen, turnoffs=map_gen['towns'], turns=0, length=(65*map_gen['towns'], 65*map_gen['towns']), width=2)
	
	#logging.debug('Placing factories...')
	#while len(map_gen['refs']['factories'])<map_gen['factories']:
	#	place_factory(map_gen)
	
	while map_gen['queued_roads']:
		_road = map_gen['queued_roads'].pop()
		_possible_next_dirs = _road['_next_dirs']
		del _road['_next_dirs']
		
		_road['next_dir'] = random.choice(_possible_next_dirs)
		_positions = chunks_in_line(_road['start_pos'], (numbers.clip(_road['next_dir'][0]*map_gen['size'][0], 0, map_gen['size'][0]-1), numbers.clip(_road['next_dir'][1]*map_gen['size'][1], 0, map_gen['size'][1]-1)), ['road'])
		_length = numbers.clip(len(_positions), 0, 15)
		
		_road['length'] = (_length/2, _length-2)
		
		place_road(map_gen, **_road)
	
	#Place dirt road leading to factories/swamp
	#TODO: Actual location of factories/swamp
	_dirt_path_start_key = alife.chunks.get_nearest_chunk_in_list((MAP_SIZE[0]/2, 150), map_gen['refs']['roads'])
	_dirt_path_end_x_pos = numbers.clip(alife.chunks.get_chunk(_dirt_path_start_key)['pos'][0]+random.randint(-50, 50),
	                                    int(round(MAP_SIZE[0]*.25)),
	                                    int(round(MAP_SIZE[0]*.75)))
	place_dirt_path(map_gen, _dirt_path_start_key, alife.chunks.get_chunk_key_at((_dirt_path_end_x_pos, 150)))
	
	logging.debug('Placing rookie village...')
	
	place_village(map_gen, map_gen['chunk_map'][alife.chunks.get_nearest_chunk_in_list(((map_gen['size'][0]/2),
	                                                                                    map_gen['size'][1]-(15*map_gen['chunk_size'])),
	                                                                                   map_gen['refs']['roads'])]['pos'])
	
	logging.debug('Placing towns...')
	for town_seed_chunk in map_gen['refs']['town_seeds']:
		_size = random.randint(map_gen['settings']['town size'][0]*(len(map_gen['refs']['towns'])+1), map_gen['settings']['town size'][1]*(len(map_gen['refs']['towns'])+1))
		place_town(map_gen, start_chunk_key=town_seed_chunk,
		           size=_size)
	
	for chunk_key in clean_chunk_map(map_gen, 'town', minimum_chunks=1):
		for town in map_gen['refs']['towns'].values():
			if chunk_key in town['chunks']:
				town['chunks'].remove(chunk_key)

def find_spaces_matching(map_gen, chunk_type, neighbor_rules):
	_chunk_keys = []
	
	for chunk_key in map_gen['chunk_map']:
		_chunk = map_gen['chunk_map'][chunk_key]
		
		if not _chunk['type'] == chunk_type:
			continue
		
		_break = False
		for rule in neighbor_rules:
			if not rule['min']<=len(get_neighbors_of_type(map_gen, _chunk['pos'], rule['chunk_type'], rule['diagonal']))<=rule['max']:
				_break = True
				break
		
		if _break:
			continue
		
		_chunk_keys.append(chunk_key)
	
	return _chunk_keys

def chunks_in_line(pos1, pos2, avoid_chunk_types):
	_chunk_keys = []
	
	for pos in drawing.diag_line(pos1, pos2):
		_chunk_key = alife.chunks.get_chunk_key_at(pos)
		_chunk = alife.chunks.get_chunk(_chunk_key)
		
		if _chunk['type'] in avoid_chunk_types:
			break
		
		if not _chunk_key in _chunk_keys:
			_chunk_keys.append(_chunk_key)
	
	return _chunk_keys

def place_road(map_gen, length=(15, 25), start_pos=None, next_dir=None, turnoffs=0, turns=-1, width=1, can_create=0, first_segment=50):
	_start_edge = 2#random.randint(0, 3)
	_town_created = False
	
	if turns == -1:
		_max_turns = random.randint(1, 3)
	else:
		_max_turns = turns
	
	_road_segments = range(random.randint(length[0], length[1]))
	_town_segments = []
	for i in range(turnoffs):
		if i:
			_segment = len(_road_segments)/(turnoffs-i)
			_segment -= 10
		else:
			_segment = first_segment
		
		_town_segments.append(_segment)
	
	_pos = start_pos
	_prev_dir = None
	_next_dir = next_dir
	
	if start_pos:
		_chunk_key = '%s,%s' % ((start_pos[0]/map_gen['chunk_size'])*map_gen['chunk_size'],
		                        (start_pos[1]/map_gen['chunk_size'])*map_gen['chunk_size'])
	
	if not _pos:
		_prev_dir = _next_dir
		
		if not _start_edge:
			_pos = [random.randint(0, map_gen['size'][0])/map_gen['chunk_size'], 0]
			_prev_dir = (0, -1)
			_next_dir = (0, 1)
		elif _start_edge == 1:
			_pos = [map_gen['size'][0]/map_gen['chunk_size'], random.randint(0, map_gen['size'][1])/map_gen['chunk_size']]
			_prev_dir = (1, 0)
			_next_dir = (-1, 0)
		elif _start_edge == 2:
			_pos = [random.randint(10*map_gen['chunk_size'], (map_gen['size'][0])/map_gen['chunk_size'])-(6*map_gen['chunk_size']), map_gen['size'][1]/map_gen['chunk_size']]
			_prev_dir = (0, 1)
			_next_dir = (0, -1)
		elif _start_edge == 3:
			_pos = [-1, random.randint(0, map_gen['size'][1])/map_gen['chunk_size']]
			_prev_dir = (-1, 0)
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
				
				if (_pos[0]+_x)*map_gen['chunk_size']>=map_gen['size'][0] or (_pos[0]+_x)*map_gen['chunk_size']<0 or (_pos[1]+_y)*map_gen['chunk_size']>=map_gen['size'][1] or (_pos[1]+_y)*map_gen['chunk_size']<0:
					continue
				
				_chunk_key = '%s,%s' % ((_pos[0]+_x)*map_gen['chunk_size'], (_pos[1]+_y)*map_gen['chunk_size'])
				map_gen['chunk_map'][_chunk_key]['type'] = 'road'
				map_gen['refs']['roads'].append(_chunk_key)
				
				print _chunk_key
			
			if i in _town_segments and len(map_gen['refs']['town_seeds'])<map_gen['towns']:
				_possible_next_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
				_possible_next_dirs.remove(_next_dir)
				
				if _prev_dir in _possible_next_dirs:
					_possible_next_dirs.remove(_prev_dir)

				#_size = map_gen['towns']-_max_turns
				#print 'road', random.randint(3, 4), _size
				
				_road = {'start_pos': _pos[:],
				         'turnoffs': 0,
				         'turns': 2,
				         'length': (25, 35),
				         'can_create': random.randint(4, 5),
				         'width': 1,
				         '_next_dirs': _possible_next_dirs}
				
				map_gen['queued_roads'].append(_road)
		
		if _max_turns:
			_possible_next_dirs = []
			if _pos[0]+len(_road_segments)+1<map_gen['size'][0]/map_gen['chunk_size']:
				_possible_next_dirs.append((1, 0))
			
			if _pos[0]-len(_road_segments)-1>0:
				_possible_next_dirs.append((-1, 0))
			
			if _pos[1]+len(_road_segments)+1<map_gen['size'][1]/map_gen['chunk_size']:
				_possible_next_dirs.append((0, 1))
			
			if _pos[1]-len(_road_segments)-1>0:
				_possible_next_dirs.append((0, -1))
				
			if not _possible_next_dirs:
				raise Exception('Road generated with no possible next direction.')
			
			_next_dir = _possible_next_dirs.pop(random.randint(0, len(_possible_next_dirs)-1))
			
			for _possible in _possible_next_dirs[:]:
				if not _next_dir[0]+_possible[0] or not _next_dir[1]+_possible[1]:
					_possible_next_dirs.remove(_possible)
			
			if can_create:
				if can_create>1:
					
					map_gen['refs']['town_seeds'].append(_chunk_key)
					_town_created = True
					
					_road = {'start_pos': _pos[:],
					         'turnoffs': 0,
					         'turns': can_create-1,
					         'can_create': can_create-1,
					         'width': 1,
					         '_next_dirs': _possible_next_dirs}
					
					map_gen['queued_roads'].append(_road)
					#place_road(map_gen, start_pos=_pos[:], turnoffs=0, length=(_length-1, _length), next_dir=random.choice(_possible_next_dirs), turns=can_create-1, can_create=can_create-1, width=1)
				
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

def place_dirt_path(map_gen, start_chunk, end_chunk):
	_start_pos = list(alife.chunks.get_chunk(start_chunk)['pos'])
	_start_pos[0]+=map_gen['chunk_size']/2
	_start_pos[1]+=map_gen['chunk_size']/2
	
	_end_pos = alife.chunks.get_chunk(end_chunk)['pos']
	
	for pos in render_los.draw_line(_start_pos[0], _start_pos[1], _end_pos[0], _end_pos[1]):
		_chunk_key = alife.chunks.get_chunk_key_at(pos)
		map_gen['chunk_map'][_chunk_key]['type'] = 'road'
		
		if not _chunk_key in map_gen['refs']['dirt_road']:
			map_gen['refs']['dirt_road'].append(_chunk_key)
		
		for pos_mod in render_los.draw_circle(pos[0], pos[1], 4):
			create_tile(map_gen, pos_mod[0], pos_mod[1], 2, random.choice(tiles.DIRT_TILES))

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

def place_village(map_gen, position, buildings=3, building_sizes=[], max_building_size=8):
	_buildings = []
	_open_chunks = []
	
	for chunk_key in get_all_connected_chunks_of_type(map_gen, alife.chunks.get_chunk_key_at(position), 'other', limit=((buildings*2)*(max_building_size))*2):
		if not maps.get_chunk(chunk_key)['type'] == 'other':
			continue
		
		_open_chunks.append(chunk_key)
	
	while buildings and _open_chunks:
		_chunk_key = random.choice(_open_chunks)
		_door_chunk_key = []
		_open_chunks.remove(_chunk_key)
		
		if building_sizes:
			_building_size = building_sizes.pop(0)
		else:
			_building_size = max_building_size
		
		_building_chunks = get_all_connected_chunks_of_type(map_gen, _chunk_key, 'other', limit=_building_size)
		
		if len(_building_chunks) < _building_size:
			continue
		
		for chunk_key in _building_chunks:
			map_gen['chunk_map'][chunk_key]['type'] = 'town'
		
		for chunk_key in _building_chunks:
			for neighbor_chunk_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'other'):
				if not neighbor_chunk_key in _building_chunks:
					_door_chunk_key = neighbor_chunk_key
					break
			
			if _door_chunk_key:
				break
		
		_buildings.append({'rooms': _building_chunks, 'exterior_chunks': [_door_chunk_key]})
		buildings -= 1
	
	map_gen['refs']['villages'].append(_buildings)

def place_town(map_gen, start_chunk_key=None, size=10):
	#Find driveways
	
	_building_map = {}
	
	#for town in map_gen['refs']['towns'].values():
		#_avoid_chunk_keys.extend(['%s,%s' % (t[0], t[1]) for t in town['chunks']])
	
	_road_seeds = []
	if start_chunk_key:
		_start_chunk = map_gen['chunk_map'][start_chunk_key]
		for road_chunk_key in get_all_connected_chunks_of_type(map_gen, start_chunk_key, 'road'):
			_road_chunk = map_gen['chunk_map'][road_chunk_key]
			
			if len(get_neighbors_of_type(map_gen, _road_chunk['pos'], 'road'))>2:
				continue
			
			if numbers.distance(_start_chunk['pos'], _road_chunk['pos'])<size*WORLD_INFO['chunk_size']:
				_road_seeds.append(road_chunk_key)
	else:
		logging.warning('No given start chunk for town. This might look weird...')
		for road_chunk_key in map_gen['refs']['roads']:
			_road_seeds.append(road_chunk_key)
	
	#Find driveways, set building seeds
	while _road_seeds:
		_chosen_key = random.choice(_road_seeds)
		
		#Choose the one with the most space surrounding it
		_best_key = {'key': None, 'score': 0, 'distance': 0}
		for _driveway_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][_chosen_key]['pos'], 'other'):
			#if get_neighbors_of_type(map_gen, map_gen['chunk_map'][_driveway_key]['pos'], 'driveway'):
			#	continue
			
			if len(get_neighbors_of_type(map_gen, map_gen['chunk_map'][_driveway_key]['pos'], 'road'))>2:
				continue
			
			_potential_driveway_chunk = map_gen['chunk_map'][_driveway_key]
			
			_score = len(get_neighbors_of_type(map_gen, map_gen['chunk_map'][_driveway_key]['pos'], 'other'))
			
			if _score<3:
				continue
			
			_distance = (size*WORLD_INFO['chunk_size'])-numbers.distance(_start_chunk['pos'], _potential_driveway_chunk['pos'])
			_score += _distance
			
			if _score > _best_key['score']:
				_best_key['key'] = _driveway_key
				_best_key['score'] = _score
				_best_key['distance'] = _distance
		
		_road_seeds.remove(_chosen_key)
		
		if not _best_key['key']:
			continue
		
		_driveway_key = _best_key['key']
		
		#Remove nearby roads from the list so we don't cluster buildings
		for _neighbor_road_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][_driveway_key]['pos'], 'road'):
			if not _neighbor_road_key in _road_seeds:
				continue
			
			_road_seeds.remove(_neighbor_road_key)
		
		#map_gen['chunk_map'][_driveway_key]['type'] = 'driveway'
		
		_building_map[_driveway_key] = {'distance': _best_key['distance']}
		
		if len(_building_map)>size/2:
			break
		
	_name = language.generate_place_name()
	map_gen['refs']['towns'].append({'name': _name, 'buildings': _building_map})

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

def place_bushes(map_gen):
	_size = (map_gen['size'][0], map_gen['size'][1], 9)
	_noise_map = generate_noise_map(_size)
	
	for y in range(0, map_gen['size'][1]-1):
		for x in range(0, map_gen['size'][0]-1):
			_chunk = map_gen['chunk_map']['%s,%s' % ((x/map_gen['chunk_size'])*map_gen['chunk_size'],
			                                (y/map_gen['chunk_size'])*map_gen['chunk_size'])]
			
			if not map_gen['map'][x][y][2]['id'] in [t['id'] for t in tiles.GRASS_TILES]:
				continue
			
			_rand = random.randint(0, _noise_map[x, y])
			
			if _rand>3:
				create_tile(map_gen, x, y, 2, random.choice(tiles.BUSH_TILES))
			elif _noise_map[x, y]<=3:
				if not random.randint(0, 50-(15*_noise_map[x, y])):
					for i in range(0, 2):
						create_tile(map_gen, x, y+i, 2, random.choice(tiles.WHEAT_TILES))
				else:
					create_tile(map_gen, x, y, 2, random.choice(tiles.FIELD_TILES))

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

def create_bush(map_gen, position, size, dither=False):
	for pos in drawing.draw_circle(position, size):
		if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
			continue
		
		if dither and random.uniform(0, 1)>numbers.distance(position, pos)/float(size):
			continue
		
		create_tile(map_gen, pos[0], pos[1], position[2], random.choice(tiles.BUSH_TILES))

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

def get_all_connected_chunks_of_type(map_gen, chunk_key, chunk_type, limit=99999):
	_connected_chunks = [chunk_key]
	_to_check = [chunk_key]
	
	while _to_check:
		_chunk_key = _to_check.pop(0)
		
		for neighbor in get_neighbors_of_type(map_gen, map_gen['chunk_map'][_chunk_key]['pos'], chunk_type):
			if neighbor in _connected_chunks:
				continue
			
			_to_check.append(neighbor)
			_connected_chunks.append(neighbor)
			
			if len(_connected_chunks) == limit:
				return _connected_chunks
	
	return _connected_chunks

def walker(map_gen, pos, moves, brush_size=1, allow_diagonal_moves=True, only_chunk_types=[], avoid_chunks=[], avoid_chunk_distance=0, return_keys=False):
	_pos = list(pos)
	_directions = [(0, -1), (-1, 0), (1, 0), (0, 1)]
	
	if allow_diagonal_moves:
		_directions.extend([(-1, -1), (1, 1), (-1, 1), (1, 1)])
	
	_walked = []
	_last_dir = {'dir': None, 'times': 0}
	for i in range(moves):
		_possible_dirs = []
		
		for _dir in _directions[:]:
			_next_pos = [_pos[0]+(_dir[0]*map_gen['chunk_size']), _pos[1]+(_dir[1]*map_gen['chunk_size'])]
			
			if _last_dir['times'] >= 3 and _next_pos == _last_dir['dir']:
				continue

			#if _next_pos in _walked:
			#	print 'stopped2'
			#	continue
			
			if _next_pos[0]<0 or _next_pos[0]>=map_gen['size'][0]-map_gen['chunk_size'] or _next_pos[1]<0 or _next_pos[1]>=map_gen['size'][1]-map_gen['chunk_size']:
				continue

			if only_chunk_types and not map_gen['chunk_map']['%s,%s' % (_next_pos[0], _next_pos[1])]['type'] in only_chunk_types:
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
				
				if only_chunk_types and not map_gen['chunk_map']['%s,%s' % (__x, __y)]['type'] in only_chunk_types:
					continue
				
				if return_keys:
					if not '%s,%s' % (__x, __y) in _walked:
						_walked.append('%s,%s' % (__x, __y))
						
						if len(_walked) == moves:
							return _walked
				elif not (__x, __y) in _walked:
					_walked.append((__x, __y))
					
					if len(_walked) == moves:
						return _walked
	
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
				if (y == size or y == map_gen['chunk_size']-size-1) and not random.randint(0, 2):
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
				if (x == size or x == map_gen['chunk_size']-size-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	#Stopped here
	elif len(_directions) == 2 and (0, -1) in _directions and (-1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if (y == map_gen['chunk_size']-size-1 or x == map_gen['chunk_size']-size-1) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 2 and (0, -1) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if (y == map_gen['chunk_size']-1 or not x) and not random.randint(0, 2):
					_tile = random.choice(tiles.GRASS_TILES)
					_height = 1
				else:
					_tile = random.choice(ground_tiles)
					_height = height
					
				for z in range(0, _height):
					create_tile(map_gen, chunk['pos'][0]+x, chunk['pos'][1]+y, 2+z, _tile)
	elif len(_directions) == 2 and (0, 1) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if (not y or not x) and not random.randint(0, 2):
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
	elif len(_directions) == 3 and (0, 1) in _directions and (-1, 0) in _directions and (1, 0) in _directions:
		for x in range(size, map_gen['chunk_size']-size):
			for y in range(size, map_gen['chunk_size']-size):
				if not y and not random.randint(0, 2):
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
								effects.create_light((x, y, 2), (255, 255, 255), 5, 0.1)

def construct_village(map_gen, buildings):
	for building in buildings:
		construct_building(map_gen, {'rooms': building['rooms']}, exterior_chunks=building['exterior_chunks'])

def construct_town(map_gen, town):
	_buildings = []
	_taken = []
	
	for building_seed in town['buildings']:
		#How much space do we have to build with?
		_first_building_key = None
		_bs = map_gen['chunk_map'][building_seed]
		
		for _nearest_road_key in get_neighbors_of_type(map_gen, _bs['pos'], 'road'):
			_direction = direction_from_key_to_key(map_gen, _nearest_road_key, building_seed)
			_first_building_key = '%s,%s' % (_bs['pos'][0]+(_direction[0]*map_gen['chunk_size']),
			                                 _bs['pos'][1]+(_direction[1]*map_gen['chunk_size']))
		
		if not _first_building_key:
			continue
		
		_to_check = [_first_building_key]
		_building_space = []
		
		if not _first_building_key in _taken:
			_building_space.append(_first_building_key)
		
		while _to_check:
			_check_chunk = map_gen['chunk_map'][_to_check.pop(len(_to_check)-1)]
			
			for empty_chunk_key in get_neighbors_of_type(map_gen, _check_chunk['pos'], 'other'):
				_continue = False
				for neighbor_chunk_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][empty_chunk_key]['pos'], 'town', diagonal=True):
					if neighbor_chunk_key in _taken:
						_continue = True
						break
				
				if _continue or empty_chunk_key in _taken:
					continue
				
				if empty_chunk_key in _building_space:
					continue
				
				if get_neighbors_of_type(map_gen, map_gen['chunk_map'][empty_chunk_key]['pos'], 'road', diagonal=True):
					continue
				
				if get_neighbors_of_type(map_gen, map_gen['chunk_map'][empty_chunk_key]['pos'], 'town', diagonal=True):
					continue
				
				if get_neighbors_of_type(map_gen, map_gen['chunk_map'][empty_chunk_key]['pos'], 'driveway', diagonal=True):
					continue
				
				_to_check.append(empty_chunk_key)
				_building_space.append(empty_chunk_key)
				_taken.append(empty_chunk_key)
				
				if len(_building_space)>=MAX_TOWNHOUSE_SIZE:
					break
			
			if len(_building_space)>=MAX_TOWNHOUSE_SIZE:
				break
		
		if not len(_building_space)>=MAX_TOWNHOUSE_SIZE:
			continue
		
		map_gen['chunk_map'][building_seed]['type'] = 'driveway'
		create_road(map_gen, building_seed, ground_tiles=tiles.CONCRETE_FLOOR_TILES, size=1)
		
		for chunk_key in _building_space:
			map_gen['chunk_map'][chunk_key]['type'] = 'town'
		
		_buildings.append({'driveway': building_seed,
		                   'rooms': _building_space[:]})
	
	for building in _buildings:
		construct_building(map_gen, building)

def construct_building(map_gen, building, building_type='town', exterior_chunks=[]):
	_main_room_types = []
	_secondary_room_types = []
	
	_wall_tile = random.choice(tiles.HOUSE_WALL_TILES)
	_building_chunk_map = {}
	for chunk_key in building['rooms']:
		_chunk = map_gen['chunk_map'][chunk_key]
		_avoid_directions = []
		_connected_interior_chunks = {}
		_connected_exterior_chunks = {}
		
		for neighbor_key in get_neighbors_of_type(map_gen, _chunk['pos'], 'any'):
			_neighbor_direction = DIRECTION_MAP[str(direction_from_key_to_key(map_gen, chunk_key, neighbor_key))]
			
			if not neighbor_key in building['rooms'] and not map_gen['chunk_map'][neighbor_key]['type'] == 'driveway' and not neighbor_key in exterior_chunks:
				_avoid_directions.append(_neighbor_direction)
				continue
			
			if map_gen['chunk_map'][neighbor_key]['type'] in [building_type]:
				_connected_interior_chunks[_neighbor_direction] = neighbor_key
			elif map_gen['chunk_map'][neighbor_key]['type'] in ['driveway'] or neighbor_key in exterior_chunks:
				_connected_exterior_chunks[_neighbor_direction] = neighbor_key
		
		_building_chunk_map[chunk_key] = {'interior_chunks': _connected_interior_chunks,
		                                  'exterior_chunks': _connected_exterior_chunks}
		
	_occupied_chunks = {}
	for chunk_key in _building_chunk_map:
		_interior_chunks = _building_chunk_map[chunk_key]['interior_chunks']
		_exterior_chunks = _building_chunk_map[chunk_key]['exterior_chunks']
		_chunk = map_gen['chunk_map'][chunk_key]
		
		#Find available room
		_lowest_neighbor = {'count': 0, 'chunk_key': None}
		_highest_neighbor = {'count': 0, 'chunk_key': None}
		
		for neighbor_key in get_neighbors_of_type(map_gen, _chunk['pos'], building_type):
			_connected_chunks = []
			
			for connected_chunk_key in get_all_connected_chunks_of_type(map_gen, neighbor_key, building_type):
				if connected_chunk_key in _occupied_chunks:
					continue
			
				_connected_chunks.append(connected_chunk_key)
			
			_remaining_free_space = len(_connected_chunks)
			if _remaining_free_space>_highest_neighbor['count'] or not _highest_neighbor['chunk_key']:
				_highest_neighbor['chunk_key'] = neighbor_key
				_highest_neighbor['count'] = _remaining_free_space
			elif _remaining_free_space<_lowest_neighbor['count'] or not _lowest_neighbor['chunk_key']:
				_lowest_neighbor['chunk_key'] = neighbor_key
				_lowest_neighbor['count'] = _remaining_free_space
		
		#Lots of connected rooms
		if _highest_neighbor['count']>=4 and _lowest_neighbor['count']>=4:
			#Higher than 4 for each
			
			#Equals means they have the same view of the house.
			if _highest_neighbor['count'] == _lowest_neighbor['count']:
				if _exterior_chunks:
					_type = 'landing'
				else:
					if len(_interior_chunks) == 1:
						_type = random.choice(['closet', 'bathroom'])
						_exterior_chunks = _interior_chunks.keys()
						_interior_chunks = []
					else:
						_type = 'hall'
				
				_occupied_chunks[chunk_key] = {'room': _type,
				                               'interior': _interior_chunks,
				                               'exterior': _exterior_chunks}
			else:
				print 'Room counts DNE'
		else:
			if _highest_neighbor['count']>1:
				#There's more than one connected node but no other available directions to build in
				#Make this a hallway or otherwise large room
				if _exterior_chunks:
					_type = 'landing'
				else:
					if len(_interior_chunks) == 1:
						_type = random.choice(['closet', 'bathroom'])
						_exterior_chunks = _interior_chunks.keys()
						_interior_chunks = []
					elif len(_interior_chunks) == 2:
						_type = 'bedroom'
						_exterior_chunks = _interior_chunks.keys()
						_interior_chunks = []
					else:
						_type = 'hall'
				
				_occupied_chunks[chunk_key] = {'room': _type,
				                               'interior': _interior_chunks,
				                               'exterior': _exterior_chunks}
				
			else:
				#There's a chance we could potentially cut off a few routes
				#Check for connected neighbors with only 1 connection
				
				_needs_to_connect = _exterior_chunks.keys()
				_can_connect_to = []
				for next_neighbor_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], building_type):
					if not next_neighbor_key in _occupied_chunks:
						continue
					
					_direction = DIRECTION_MAP[str(direction_from_key_to_key(map_gen, chunk_key, next_neighbor_key))]
					_exits = len(_occupied_chunks[next_neighbor_key]['interior'])+len(_occupied_chunks[next_neighbor_key]['exterior'])
					
					if _exits==1:
						_needs_to_connect.append(_direction)
					elif _exits>1:
						_can_connect_to.append(_direction)
				
				if _needs_to_connect and len(_can_connect_to):
					_occupied_chunks[chunk_key] = {'room': 'small1',
						                          'interior': random.sample(_can_connect_to, random.randint(1, len(_can_connect_to))),
						                          'exterior': _needs_to_connect}
				elif _interior_chunks:
					_exterior_chunks = [random.choice(_interior_chunks.keys())]
					_occupied_chunks[chunk_key] = {'room': 'small2',
						                          'interior': [],
						                          'exterior': _exterior_chunks}
				else:
					continue
		
	for chunk_key in _occupied_chunks:
		_possible_buildings = []
		_room = _occupied_chunks[chunk_key]['room']
		_interior_chunks = _occupied_chunks[chunk_key]['interior']
		_exterior_chunks = _occupied_chunks[chunk_key]['exterior']
		_chunk = map_gen['chunk_map'][chunk_key]
		
		for possible_building in map_gen['buildings']:
			_unchecked_directions = ['top', 'bot', 'left', 'right']
			_continue = False
			
			for direction in _interior_chunks:
				if not possible_building['open'][direction]:
					_continue = True
					break
				
				_unchecked_directions.remove(direction)
			
			if _continue:
				continue
			
			for direction in _exterior_chunks:
				if not possible_building['door'][direction]:
					_continue = True
					break
				
				_unchecked_directions.remove(direction)
			
			for direction in _unchecked_directions:
				if possible_building['open'][direction] or possible_building['door'][direction]:
					_continue = True
					break
			
			if _continue:
				continue
			
			_possible_buildings.append(possible_building['building'])
		
		_items = []
		_storage = []
		if _room == 'closet':
			_storage_items = [{'item': 'blue jeans', 'rarity': 1.0},
				     {'item': 'leather backpack', 'rarity': 0.65},
				     {'item': 'sneakers', 'rarity': 1.0},
				     {'item': 'white t-shirt', 'rarity': 1.0},
				     {'item': 'white cloth', 'rarity': 0.4},
			         {'item': 'glock', 'rarity': 0.25},
			         {'item': '9x19mm magazine', 'rarity': 0.3}]
			_storage = [{'item': 'wooden dresser', 'rarity': 1.0, 'spawn_list': _storage_items}]
			_floor_tiles = tiles.CONCRETE_FLOOR_TILES
		elif _room == 'bathroom':
			_floor_tiles = tiles.BLUE_FLOOR_TILES
		elif _room == 'bedroom':
			_items = [{'item': 'bed', 'rarity': 1.0},
			          {'item': 'wooden dresser', 'rarity': 0.5}]
			_storage_items = [{'item': 'blue jeans', 'rarity': 1.0},
				     {'item': 'leather backpack', 'rarity': 0.65},
				     {'item': 'sneakers', 'rarity': 1.0},
				     {'item': 'white t-shirt', 'rarity': 1.0},
				     {'item': 'white cloth', 'rarity': 0.4},
			         {'item': 'glock', 'rarity': 0.25},
			         {'item': '9x19mm magazine', 'rarity': 0.3}]
			_storage = [{'item': 'wooden dresser', 'rarity': 1.0, 'spawn_list': _storage_items}]
			_floor_tiles = tiles.DARK_BLUE_FLOOR_TILES
		elif _room == 'small1':
			_floor_tiles = tiles.BLUE_CARPET_TILES
		elif _room == 'small2':
			_floor_tiles = tiles.DARK_GREEN_FLOOR_TILES
			_items = [{'item': 'bed', 'rarity': 1.0}]
			_storage_items = [{'item': 'blue jeans', 'rarity': 1.0},
				     {'item': 'leather backpack', 'rarity': 0.65},
				     {'item': 'sneakers', 'rarity': 1.0},
				     {'item': 'white t-shirt', 'rarity': 1.0},
				     {'item': 'white cloth', 'rarity': 0.4}]
			_storage = [{'item': 'wooden dresser', 'rarity': 1.0, 'spawn_list': _storage_items}]
		elif _room == 'landing':
			_items = [{'item': 'coat rack', 'rarity': 1.0}]
			_storage_items = [{'item': 'leather backpack', 'rarity': 0.65},
			          {'item': 'sneakers', 'rarity': 1.0}]
			
			_storage = [{'item': 'wooden dresser', 'rarity': 1.0, 'spawn_list': _storage_items}]
			          
			_floor_tiles = tiles.WHITE_TILE_TILES
		else:
			_floor_tiles = tiles.SEA_CARPET_TILES
		
		_neighbor_dirs = [DIRECTION_MAP[str(d)] for d in [direction_from_key_to_key(map_gen, chunk_key, n) for n in get_neighbors_of_type(map_gen, _chunk['pos'], building_type)]]
		
		try:
			_building = random.choice(_possible_buildings)
		except:
			_int = ', '.join(_interior_directions)
			_ext = ', '.join(_exterior_directions)
			
			raise Exception('Matching tile not found for the following layout: Interior-facing: %s, Exterior-facing: %s, Doors: %s' % (_int, _ext, _rules['doors']))
		
		_half = map_gen['chunk_size']/2
		_open_spots = []
		for _y in range(map_gen['chunk_size']):
			y = _chunk['pos'][1]+_y
			for _x in range(map_gen['chunk_size']):
				x = _chunk['pos'][0]+_x
				
				for i in range(3):
					if i == 2:
						create_tile(map_gen, x, y, 2+i, _wall_tile)
					elif _building[_y][_x] == '#':
						create_tile(map_gen, x, y, 2+i, _wall_tile)
					elif i in [0] and _building[_y][_x] == 'D':
						items.create_item('wooden door', position=[x, y, 2+i])
						create_tile(map_gen, x, y, 2+i, random.choice(_floor_tiles))
					elif i in [0] and _building[_y][_x] == '.':
						create_tile(map_gen, x, y, 2+i, random.choice(_floor_tiles))
						
						if not i and random.randint(0, 500) == 500:
							effects.create_light((x, y, 2), (255, 255, 255), 5, 0.95)
						
						_open_spots.append((x, y))
						
		_possible_spots = []
		for pos in _open_spots:
			_open = 0
			_continue = False
			
			for _n_pos in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
				for item in items.get_items_at((pos[0]+_n_pos[0], pos[1]+_n_pos[1], 2)):
					if item['type'] == 'door':
						_continue = True
						break
				
				if _continue:
					break
				
				if (pos[0]+_n_pos[0], pos[1]+_n_pos[1]) in _open_spots:
					_open += 1
			
			if _continue:
				continue
			
			_possible_spots.append({'spot': pos[:], 'open_neighbors': _open})
		
		_only_one_neighbor = []
		for entry in _possible_spots:
			if entry['open_neighbors'] == 3:
				_only_one_neighbor.append(entry)
		
		if not _only_one_neighbor:
			continue
		
		_placed_containers = []
		if _storage:
			_spawn_x, _spawn_y = random.choice([s['spot'] for s in _only_one_neighbor])
			
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
		
		if _items:
			for item in _items:
				if not item['rarity']>random.uniform(0, 1.0):
					continue
				
				_spawn_x, _spawn_y = random.choice([s['spot'] for s in _only_one_neighbor])
				items.create_item(item['item'], position=[_spawn_x, _spawn_y, 2])
		
		for container in _placed_containers:
			_storage.remove(container)
	
	return _building_chunk_map

def construct_outpost(map_gen):
	_chunk_keys = map_gen['chunk_map'].keys()
	_outpost_chunk = None
	
	while _chunk_keys:
		_chunk_key = _chunk_keys.pop(random.randint(0, len(_chunk_keys)-1))
		_chunk = map_gen['chunk_map'][_chunk_key]
		
		_dirt_road_chunks = []
		_dirt_road_end_pos = alife.chunks.get_chunk(map_gen['refs']['dirt_road'][len(map_gen['refs']['dirt_road'])-1])['pos']
		
		for chunk_key in map_gen['refs']['dirt_road']:
			if numbers.distance(alife.chunks.get_chunk(chunk_key)['pos'], _dirt_road_end_pos)>6*5:
				continue
			
			_dirt_road_chunks.append(chunk_key)
		
		if alife.chunks.get_distance_to_nearest_chunk_in_list(_chunk['pos'], _dirt_road_chunks)>OUTPOST_DISTANCE:
			continue
		
		_continue = False
		for _outpost_chunks in map_gen['refs']['outposts']:
			if alife.chunks.get_distance_to_nearest_chunk_in_list(_chunk['pos'], _outpost_chunks)<15*5:
				_continue = True
				continue
		
		if _continue:
			continue
		
		_outpost_chunk = _chunk
		break
	
	if not _outpost_chunk:
		raise Exception('No more room for outposts.')
	
	_building_chunks = walker(map_gen, _outpost_chunk['pos'], random.randint(11, 15), allow_diagonal_moves=False, return_keys=True, brush_size=2)
	
	for chunk_key in _building_chunks:
		map_gen['chunk_map'][chunk_key]['type'] = 'outpost'
	
	_wall_chunks = []
	_yard_chunks = []
	for chunk_key in _building_chunks:	
		for neighbor_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'other', diagonal=True):
			_wall_chunks.append(neighbor_key)
			_yard_chunks.extend(get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor_key]['pos'], 'other'))	
	
	_door_chunk_key = random.choice(_wall_chunks)
	
	for chunk_key in _wall_chunks:
		if chunk_key == _door_chunk_key:
			continue
		
		map_gen['chunk_map'][chunk_key]['type'] = 'wall'
	
	for chunk_key in _yard_chunks[:]:
		_pos = map_gen['chunk_map'][chunk_key]['pos']
		
		for new_chunk_key in walker(map_gen, _pos, 8, return_keys=True):
			if not new_chunk_key in _yard_chunks:
				_yard_chunks.append(new_chunk_key)
	
	if _door_chunk_key in _yard_chunks:
		_yard_chunks.remove(_door_chunk_key)
	
	for chunk_key in _yard_chunks:
		if map_gen['chunk_map'][chunk_key]['type'] == 'wall':
			continue
		
		_pos = map_gen['chunk_map'][chunk_key]['pos']
		map_gen['chunk_map'][chunk_key]['type'] = 'outpost'
		
		#Dither
		_dither_in = [direction_from_key_to_key(map_gen, chunk_key, key) for key in get_neighbors_of_type(map_gen, _pos, 'other')]
		
		for y in range(map_gen['chunk_size']):
			for x in range(map_gen['chunk_size']):
				
				_continue = False
				for _dither_dir in _dither_in:
					if x < map_gen['chunk_size']+(_dither_dir[0]*(map_gen['chunk_size']/2)) or y < map_gen['chunk_size']+(_dither_dir[1]*(map_gen['chunk_size']/2)):
						if not random.randint(0, 3):
							create_tile(map_gen, _pos[0]+x, _pos[1]+y, 2, random.choice(tiles.BROKEN_CONCRETE_FLOOR_TILES))
							
							_continue = True
							break
				
				if _continue:
					continue
				
				_tile = map_gen['map'][_pos[0]+x][_pos[1]+y][3]
				
				if not _tile or (not _tile['id'] in [t['id'] for t in tiles.GRASS_TILES] and not _tile['id'] in [t['id'] for t in tiles.FIELD_TILES]):
					create_tile(map_gen, _pos[0]+x, _pos[1]+y, 2, random.choice(tiles.CONCRETE_FLOOR_TILES))
		
		if not random.randint(0, 5):
			for y in range(2, 4):
				for x in range(2, 4):
					for z in range(0, 2):
						create_tile(map_gen, _pos[0]+x, _pos[1]+y, 2+z, random.choice(tiles.WHITE_TILE_TILES))	
	
	
	for chunk_key in _wall_chunks:
		if chunk_key == _door_chunk_key:
			continue
		
		_xy_swap_x = -1
		_xy_swap_y = -1
		_pos = map_gen['chunk_map'][chunk_key]['pos']
		_directions = [DIRECTION_MAP[k] for k in [str(direction_from_key_to_key(map_gen, chunk_key, k)) for k in get_neighbors_of_type(map_gen,  map_gen['chunk_map'][chunk_key]['pos'], 'wall') if not k == _door_chunk_key]]
		
		if 'left' in _directions and 'right' in _directions or (len(_directions)==1 and ('left' in _directions or 'right' in _directions)):
			_x_min = 0
			_x_max = map_gen['chunk_size']
			_y_min = 2
			_y_max = 2
		elif 'top' in _directions and 'bot' in _directions or (len(_directions)==1 and ('top' in _directions or 'bot' in _directions)):
			_x_min = 2
			_x_max = 2
			_y_min = 0
			_y_max = map_gen['chunk_size']
		elif 'left' in _directions and 'top' in _directions:
			_x_min = 0
			_x_max = map_gen['chunk_size']
			_y_min = 2
			_y_max = 2
			_xy_swap_x = 2
		else:
			continue
		
		_swapped = False
		for x in range(0, map_gen['chunk_size']):
			_tile = tiles.WALL_TILE
			
			if x<_x_min or x>_x_max:
				continue
			
			if _swapped:
				_x = _pos[0]-x
			else:
				_x = _pos[0]+x
			
			for y in range(0, map_gen['chunk_size']):
				if _swapped:
					_tile = tiles.RED_BRICK_1
					_y = _pos[1]-y
				else:
					_y = _pos[1]+y
				
				if (x == _xy_swap_x or y == _xy_swap_y) and not _swapped:
					_swapped = True
				
				if y<_y_min or y>_y_max:
					continue
				
				create_tile(map_gen, _x, _y, 2, _tile)
	
	map_gen['refs']['outposts'].append(_building_chunks)
	_building_chunk_keys = construct_building(map_gen, {'rooms': _building_chunks}, building_type='outpost', exterior_chunks=[_door_chunk_key])
	
	for chunk_key in _building_chunks:
		for neighbor_chunk_key in get_neighbors_of_type(map_gen, map_gen['chunk_map'][chunk_key]['pos'], 'wall', diagonal=True):
			for y in range(map_gen['chunk_size']):
				for x in range(map_gen['chunk_size']):
					_pos = list(map_gen['chunk_map'][neighbor_chunk_key]['pos'])
					_pos[0] += x
					_pos[1] += y
					
					if not map_gen['map'][_pos[0]][_pos[1]][2]['id'] in [t['id'] for t in tiles.GRASS_TILES]:
						continue
					
					create_tile(map_gen, _pos[0], _pos[1], 2, random.choice(tiles.CONCRETE_FLOOR_TILES))

def can_spawn_item(item):
	if item['rarity']>random.uniform(0, 1.0):
		return True
	
	return False

def create_region_spawns():
	pass

def fill_empty_spaces(map_gen):
	_empty_spots = []
	
	for chunk_key in map_gen['chunk_map']:
		_chunk = map_gen['chunk_map'][chunk_key]
		
		if not _chunk['type'] == 'other':
			continue
		
		_empty_spots.append(chunk_key)

def decorate_world(map_gen):
	#Side roads
	logging.debug('Generating side roads...')
	_rules = [{'chunk_type': 'town', 'diagonal': True, 'min': 1, 'max': 7},
	          {'chunk_type': 'road', 'diagonal': True, 'min': 0, 'max': 0}]
	
	_side_road_chunks = find_spaces_matching(map_gen, 'other', _rules)
	
	for chunk_key in _side_road_chunks:
		map_gen['chunk_map'][chunk_key]['type'] = 'road'
	
	for chunk_key in _side_road_chunks:
		if random.randint(0, 5) and len(get_all_connected_chunks_of_type(map_gen, chunk_key, 'road'))<=5:
			map_gen['chunk_map'][chunk_key]['type'] = 'other'
			continue
		
		create_road(map_gen, chunk_key, size=0, ground_tiles=tiles.CONCRETE_FLOOR_TILES)
	
	#place_bushes(map_gen)
	
	#backyards
	for town in map_gen['refs']['towns']:
		if not map_gen['settings']['back yards']:
			break
		
		_backyard = []
		for chunk_key in town['buildings']:
			_chunk = map_gen['chunk_map'][chunk_key]
			for neighbor in get_neighbors_of_type(map_gen, _chunk['pos'], 'other', diagonal=True):
				if get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor]['pos'], 'road', diagonal=False):
					continue
				
				if not get_neighbors_of_type(map_gen, map_gen['chunk_map'][neighbor]['pos'], 'driveway', diagonal=False):
					_backyard.append(neighbor)
		
		for chunk_key in _backyard:
			_chunk = map_gen['chunk_map'][chunk_key]
			_chunk['type'] = 'backyard'
			_pos = (_chunk['pos'][0]+random.randint(0, map_gen['chunk_size']-1),
			        _chunk['pos'][1]+random.randint(0, map_gen['chunk_size']-1), 2)
			
			create_tree(map_gen, _pos, random.randint(4, 7))
	
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

def round_off_edges(map_gen):
	#Round off those fields
	_rules = [{'chunk_type': 'road', 'min': 1, 'max': 4, 'diagonal': False}]

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
	SETTINGS['running'] = False
	
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
		generate_map(size=(250, 250, 10), towns=1, factories=0, outposts=2, forests=1, skip_zoning=(not '--zone' in sys.argv), skip_chunking=(not '--chunk' in sys.argv))
	
	print 'Total mapgen time:', time.time()-_t