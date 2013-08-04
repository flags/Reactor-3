from globals import *

import alife
import maps

import random

TOWN_DISTANCE = 45

def generate_map(size=(256, 256, 10), detail=4, towns=3, forests=2, underground=True):
	""" Size: Both width and height must be divisible by DETAIL.
	Detail: Determines the chunk size. Smaller numbers will generate more elaborate designs.
	Towns: Decides the amount of towns generated.
	Forests: Number of large forested areas.
	Underground: Flags whether buildings can be constructed beneath the surface.
	"""
	
	map_gen = {'size': size,
		'detail': detail,
		'towns': towns,
		'underground': underground,
	     'chunk_map': {},
	     'refs': {'towns': []},
	     'map': maps.create_map(size=size)}
	
	return map_gen

def generate_chunk_map(map_gen):
	for y1 in xrange(0, MAP_SIZE[1], WORLD_INFO['chunk_size']):
		for x1 in xrange(0, MAP_SIZE[0], WORLD_INFO['chunk_size']):
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
			     'pos': alife.chunks.get_chunk_pos(_chunk_key)}
			
def generate_outlines(map_gen):
	#for y1 in range(0, MAP_SIZE[1], WORLD_INFO['chunk_size']):
	while len(map_gen['refs']['towns'])<map_gen['towns']:
		place_town(map_gen)
			
		#if 'building' in _tiles and _tiles['building']>=15:
		#	map_gen['chunk_map'][_chunk_key]['type'] = 'building'
		#elif 'road' in _tiles and _tiles['road']>=15:
		#	map_gen['chunk_map'][_chunk_key]['type'] = 'road'
		#else:
		#	map_gen['chunk_map'][_chunk_key]['type'] = 'other'

def place_town(map_gen):
	_existing_towns = map_gen['refs']['towns']
	
	while 1:
		_town_chunk = random.choice(map_gen['chunk_map'].values())
				
		if alife.chunks.get_distance_to_hearest_chunk_in_list(_town_chunk['pos'], _existing_towns) > TOWN_DISTANCE:
			continue
		
		walker(map_gen,
			_town_chunk['pos'],
			'town',
		     20,
			allow_diagonal_moves=False,
			avoid_chunks=_existing_towns,
			avoid_chunk_distance=TOWN_DISTANCE)
		
def walker(map_gen, pos, chunk_type, moves, density=5, allow_diagonal_moves=True, avoid_chunks=[], avoid_chunk_distance=0):
	_pos = list(pos)
	_directions = [(0, -1), (-1, 0), (1, 0), (0, 1)]
	
	if allow_diagonal_moves:
		_directions.extend([(-1, -1), (1, 1), (-1, 1), (1, 1)])
	
	for i in range(moves):
		for _dir in _directions[:]:
			_next_pos = (_pos[0]+(_dir[0]*map_gen['chunk_size']), _pos[1]+(_dir[1]*map_gen['chunk_size']))
			
			if _next_pos[0]<0 or _next_pos[0]>=map_gen['size'][0] or _next_pos[1]<0 or _next_pos[1]>=map_gen['size'][1]:
				continue
			
			if alife.chunks.get_distance_to_hearest_chunk_in_list(_next_pos, avoid_chunks) > avoid_chunk_distance:
				continue
			
			_possible_dirs.append(_next_pos)
			
		if not _possible_dirs:
			return False
	
	