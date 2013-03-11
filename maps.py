from globals import *
from tiles import *

import life as lfe

import alife

import graphics as gfx
import maputils
import logging
import numbers
import drawing
import random
import numpy
import copy
import time
import json
import os

try:
	import render_los as cython_render_los
	CYTHON_ENABLED = True
	
except ImportError, e:
	CYTHON_ENABLED = False
	logging.warning('[Cython] ImportError with module: %s' % e)
	logging.warning('[Cython] Certain functions can run faster if compiled with Cython.')
	logging.warning('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')

def create_map():
	_map = []

	for x in range(MAP_SIZE[0]):
		_y = []
		for y in range(MAP_SIZE[1]):
			_z = []
			for z in range(MAP_SIZE[2]):
				if z == 2:
					_z.append(create_tile(random.choice(
						[TALL_GRASS_TILE,SHORT_GRASS_TILE,GRASS_TILE])))
				else:
					_z.append(None)

			_y.append(_z)
		_map.append(_y)

	gfx.log('Created new map of size (%s,%s).' % (MAP_SIZE[0],MAP_SIZE[1]))
	return _map

def save_map(map_name,map):
	_map_dir = os.path.join(DATA_DIR,'maps')

	try:
		os.mkdir(_map_dir)
	except:
		pass

	with open(os.path.join(_map_dir,map_name),'w') as _map_file:
		try:
			_map_file.write(json.dumps(map))
			logging.info('Map \'%s\' saved.' % map_name)
			gfx.log('Map \'%s\' saved.' % map_name)
		except TypeError:
			logging.critical('FATAL: Map not JSON serializable.')
			gfx.log('TypeError: Failed to save map (Map not JSON serializable).')

def load_map(map_name):
	_map_dir = os.path.join(DATA_DIR,'maps')

	with open(os.path.join(_map_dir,map_name),'r') as _map_file:
		try:
			_map_string = json.loads(_map_file.readline())
			_map_size = maputils.get_map_size(_map_string)
			MAP_SIZE[0] = _map_size[0]
			MAP_SIZE[1] = _map_size[1]
			MAP_SIZE[2] = _map_size[2]
			
			logging.info('Map \'%s\' loaded.' % map_name)
			gfx.log('Map \'%s\' loaded.' % map_name)

			return _map_string
		except TypeError:
			logging.error('FATAL: Map not JSON serializable.')
			gfx.log('TypeError: Failed to save map (Map not JSON serializable).')

def reset_lights():
	RGB_LIGHT_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	RGB_LIGHT_BUFFER[1] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	RGB_LIGHT_BUFFER[2] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))

def render_lights(source_map):
	if not SETTINGS['draw lights']:
		return False

	reset_lights()
	RGB_LIGHT_BUFFER[0] = numpy.add(RGB_LIGHT_BUFFER[0], SUN_BRIGHTNESS[0])
	RGB_LIGHT_BUFFER[1] = numpy.add(RGB_LIGHT_BUFFER[1], SUN_BRIGHTNESS[0])
	RGB_LIGHT_BUFFER[2] = numpy.add(RGB_LIGHT_BUFFER[2], SUN_BRIGHTNESS[0])
	(x, y) = numpy.meshgrid(range(MAP_WINDOW_SIZE[0]), range(MAP_WINDOW_SIZE[1]))

	for light in LIGHTS:
		_render_x = light['x']-CAMERA_POS[0]
		_render_y = light['y']-CAMERA_POS[1]
		_x = numbers.clip(light['x']-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0])
		_y = numbers.clip(light['y']-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1])
		_top_left = (_x,_y,light['z'])
		
		los = cython_render_los.render_los(source_map,(light['x'],light['y']),top_left=_top_left)
		print numpy.r_[los[0][:-CAMERA_POS[0]],0].shape
		#print los.shape
		
		sqr_distance = (x - (light['x']-CAMERA_POS[0]))**2 + (y - (light['y']-CAMERA_POS[1]))**2
		
		brightness = light['brightness'] / sqr_distance
		brightness = numpy.clip(brightness * 255, 0, 255)
		brightness *= los
		
		
		#RGB_LIGHT_BUFFER[0] = RGB_LIGHT_BUFFER[0]*los
		#RGB_LIGHT_BUFFER[1] = RGB_LIGHT_BUFFER[1]*los
		#RGB_LIGHT_BUFFER[2] = RGB_LIGHT_BUFFER[2]*los

		RGB_LIGHT_BUFFER[0] = numpy.subtract(RGB_LIGHT_BUFFER[0],brightness).clip(0,255)
		RGB_LIGHT_BUFFER[1] = numpy.subtract(RGB_LIGHT_BUFFER[1],brightness).clip(0,255)
		RGB_LIGHT_BUFFER[2] = numpy.subtract(RGB_LIGHT_BUFFER[2],brightness).clip(0,255)

def _render_los(map,pos,cython=False):
	if cython:
		return cython_render_los.render_los(map,pos)
	else:
		return render_los(map,pos)

def render_los(map,position,los_buffer=LOS_BUFFER[0]):
	los_buffer = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	
	for pos1 in drawing.draw_circle(position,SETTINGS['los']):

		_dark = False
		for pos in drawing.diag_line(position,pos1):
			_x = pos[0]-CAMERA_POS[0]
			_y = pos[1]-CAMERA_POS[1]
			
			if _x<0 or _x>=MAP_WINDOW_SIZE[0] or _y<0 or _y>=MAP_WINDOW_SIZE[1]:
				continue
			
			if map[pos[0]][pos[1]][CAMERA_POS[2]+1]:				
				if not _dark:
					_dark = True
					los_buffer[_y,_x] = 1
					
					continue
				
			if _dark:
				continue

			los_buffer[_y,_x] = 1

def render_map(map):
	_X_MAX = CAMERA_POS[0]+MAP_WINDOW_SIZE[0]
	_Y_MAX = CAMERA_POS[1]+MAP_WINDOW_SIZE[1]
	
	DARK_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	LIGHT_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))

	if _X_MAX>MAP_SIZE[0]:
		_X_MAX = MAP_SIZE[0]

	if _Y_MAX>MAP_SIZE[1]:
		_Y_MAX = MAP_SIZE[1]

	for x in range(CAMERA_POS[0],_X_MAX):
		_RENDER_X = x-CAMERA_POS[0]
		for y in range(CAMERA_POS[1],_Y_MAX):
			_RENDER_Y = y-CAMERA_POS[1]
			_drawn = False
			for z in range(MAP_SIZE[2]-1,-1,-1):
				if map[x][y][z]:
					if z > CAMERA_POS[2] and SETTINGS['draw z-levels above'] and not LOS_BUFFER[0][_RENDER_Y,_RENDER_X]:
						gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
						gfx.darken_tile(_RENDER_X,_RENDER_Y,abs((CAMERA_POS[2]-z))*30)
						_drawn = True
					elif z == CAMERA_POS[2]:
						if (x,y,z) in SELECTED_TILES[0] and time.time()%1>=0.5:
							gfx.blit_char(_RENDER_X,
								_RENDER_Y,
								'X',
								darker_grey,
								black,
								char_buffer=MAP_CHAR_BUFFER,
								rgb_fore_buffer=MAP_RGB_FORE_BUFFER,
								rgb_back_buffer=MAP_RGB_BACK_BUFFER)
						else:
							gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
						_drawn = True
					elif z < CAMERA_POS[2] and SETTINGS['draw z-levels below']:
						gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
						gfx.darken_tile(_RENDER_X,_RENDER_Y,abs((CAMERA_POS[2]-z))*30)
						_drawn = True
				
					if SETTINGS['draw z-levels above'] and _drawn:
						break
			
			if not _drawn:
				gfx.blit_tile(_RENDER_X,_RENDER_Y,BLANK_TILE)

#TODO: Put both of these into one function.
def render_x_cutout(map,x_pos,y_pos):
	_X_MAX = x_pos+X_CUTOUT_WINDOW_SIZE[0]
	y = y_pos
	
	for x in range(x_pos,_X_MAX):
		if x>=MAP_SIZE[0] or x<0:
			continue
		
		_RENDER_X = x-x_pos
		for z in range(MAP_SIZE[2]-3):
			if map[x][y][z]:
				_tile = map[x][y][z]
			else:
				_tile = BLANK_TILE
			
			gfx.blit_tile(_RENDER_X,
				(MAP_SIZE[2]-3)-z,
				_tile,
				char_buffer=X_CUTOUT_CHAR_BUFFER,
				rgb_fore_buffer=X_CUTOUT_RGB_FORE_BUFFER,
				rgb_back_buffer=X_CUTOUT_RGB_BACK_BUFFER)

def render_y_cutout(map,x_pos,y_pos):
	_Y_MAX = y_pos+Y_CUTOUT_WINDOW_SIZE[1]
	x = x_pos
	
	for y in range(y_pos,_Y_MAX):
		if y>=MAP_SIZE[1] or y<0:
			break
		
		_RENDER_Y = y-y_pos
		for z in range(MAP_SIZE[2]):
			if map[x][y][z]:
				_tile = map[x][y][z]
			else:
				_tile = BLANK_TILE
			
			gfx.blit_tile(_RENDER_Y,
				MAP_SIZE[2]-z,
				_tile,
				char_buffer=Y_CUTOUT_CHAR_BUFFER,
				rgb_fore_buffer=Y_CUTOUT_RGB_FORE_BUFFER,
				rgb_back_buffer=Y_CUTOUT_RGB_BACK_BUFFER)

def render_shadows(map):
	_stime = time.time()
	_X_MAX = CAMERA_POS[0]+MAP_WINDOW_SIZE[0]
	_Y_MAX = CAMERA_POS[1]+MAP_WINDOW_SIZE[1]

	if _X_MAX>MAP_SIZE[0]:
		_X_MAX = MAP_SIZE[0]

	if _Y_MAX>MAP_SIZE[1]:
		_Y_MAX = MAP_SIZE[1]

	for x in range(CAMERA_POS[0],_X_MAX):
		_RENDER_X = x-CAMERA_POS[0]
		for y in range(CAMERA_POS[1],_Y_MAX):
			_RENDER_Y = y-CAMERA_POS[1]
			_zlock = -1
			
			for pos in drawing.draw_3d_line(SUN_POS,(x,y,2)):
				pos = list(pos)
				_actual_pos = (pos[0]-CAMERA_POS[0],pos[1]-CAMERA_POS[1])
				
				if _actual_pos[0] < 0:
					continue
				
				if pos[2] >= MAP_SIZE[2]:
					continue
				
				if pos[0] >= MAP_WINDOW_SIZE[0]:
					continue
				
				if pos[1] >= MAP_WINDOW_SIZE[1]:
					continue
				
				if _zlock>=0 and not pos[2]==_zlock:
					break
				
				if map[pos[0]][pos[1]][pos[2]]:
					_zlock = pos[2]
					gfx.darken_tile(_actual_pos[0],_actual_pos[1],50)
					gfx.lighten_tile(_actual_pos[0],_actual_pos[1],(pos[2]*20))

def soften_shadows(map):
	global DARK_BUFFER
	
	_X_MAX = CAMERA_POS[0]+MAP_WINDOW_SIZE[0]
	_Y_MAX = CAMERA_POS[1]+MAP_WINDOW_SIZE[1]
	
	_DARK_BUFFER_COPY = numpy.copy(DARK_BUFFER)

	if _X_MAX>MAP_SIZE[0]:
		_X_MAX = MAP_SIZE[0]

	if _Y_MAX>MAP_SIZE[1]:
		_Y_MAX = MAP_SIZE[1]

	for r in range(1):
		for x in range(CAMERA_POS[0],_X_MAX):
			_RENDER_X = x-CAMERA_POS[0]
			for y in range(CAMERA_POS[1],_Y_MAX):
				_RENDER_Y = y-CAMERA_POS[1]
				
				for x1 in range(-1,2):
					for y1 in range(-1,2):
						if not x1 and not y1:
							continue
						
						if _RENDER_X+x1<0 or _RENDER_X+x1>=MAP_WINDOW_SIZE[0]:
							continue
						
						if _RENDER_Y+y1<0 or _RENDER_Y+y1>=MAP_WINDOW_SIZE[1]:
							continue
						
						_near_dark = DARK_BUFFER[0][_RENDER_Y+y1,_RENDER_X+x1]
						
						#print _near_dark,DARK_BUFFER[0][_RENDER_Y,_RENDER_X]
						if _near_dark<DARK_BUFFER[0][_RENDER_Y,_RENDER_X]:
							_DARK_BUFFER_COPY[0][_RENDER_Y,_RENDER_X] = 50#255-abs((_DARK_BUFFER_COPY[0][_RENDER_Y,_RENDER_X]-_near_dark))
		
		DARK_BUFFER[0] = numpy.copy(_DARK_BUFFER_COPY)[0]

def flood_select_by_tile(map_array,tile_id,where,fuzzy=True):
	_to_check = [where]
	_checked = []
	
	while _to_check:
		_current = _to_check.pop(0)
		
		if not _current in _checked:
			_checked.append(_current)
		
		for _x in range(-1,2):
			for _y in range(-1,2):
				x = _x+_current[0]
				y = _y+_current[1]
				z = _current[2]
				
				if fuzzy:
					if map_array[x][y][z] and map_array[x][y][z]['id'].count(tile_id):
						if not (x,y,z) in _checked and not (x,y,z) in _to_check:
							_to_check.append((x,y,z))
				else:
					if map_array[x][y][z] and map_array[x][y][z]['id'] == tile_id:
						if not (x,y,z) in _checked:
							_to_check.append((x,y,z))
	
	return _checked

def get_collision_map(map_array,start,end,mark=1):
	x_size = end[0]-start[0]
	y_size = end[1]-start[1]
	z = start[2]
	
	collision_map = numpy.zeros((x_size,y_size))
	
	for x in range(x_size):
		for y in range(y_size):
			
			if map_array[x][y][z+1]:# and map_array[x][y][z+2]:
				collision_map[y,x] = mark
	
	return collision_map

def get_chunk(chunk_id):
	return CHUNK_MAP[chunk_id]

def refresh_chunk(chunk_id):
	chunk = get_chunk(chunk_id)
	
	_life = []
	for life in LIFE:
		if alife.chunks.is_in_chunk(life, chunk_id):
			_life.append(life['id'])
	
	_items = []
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if item.has_key('id'):
			continue
		
		if alife.chunks.is_in_chunk(item, chunk_id):
			_items.append(_item)
		
	chunk['items'] = _items[:]
	
	chunk['digest'] = '%s-P=%s-I=%s' % ('%s,%s' % (chunk['pos'][0],chunk['pos'][1]), _life, _item)
	broadcast_chunk_change(chunk_id)

def broadcast_chunk_change(chunk_id):
	for life in LIFE:
		for known_chunk_key in life['known_chunks']:
			_chunk = get_chunk(known_chunk_key)
			_known_chunk = life['known_chunks'][known_chunk_key]
			
			if _chunk['digest'] == _known_chunk['digest']:
				continue
			
			_known_chunk['digest'] = _chunk['digest']
			
			#logging.debug('%s got update for chunk #%s' % (' '.join(life['name']), '%s,%s' % (_chunk['pos'][0],_chunk['pos'][1])))

def get_open_position_in_chunk(source_map, chunk_id):
	_chunk = get_chunk(chunk_id)
	
	for x1 in range(SETTINGS['chunk size']):
		for y1 in range(SETTINGS['chunk size']):
			x = x1+_chunk['pos'][0]
			y = y1+_chunk['pos'][1]
			
			if source_map[x][y][2] and not source_map[x][y][3]:
				return (x, y)
	
	return False

def update_chunk_map(source_map):
	_stime = time.time()
	_chunk_map = {}
	
	for y1 in range(0, MAP_SIZE[1], SETTINGS['chunk size']):
		for x1 in range(0, MAP_SIZE[0], SETTINGS['chunk size']):
			_chunk_key = '%s,%s' % (x1, y1)
			_chunk_map[_chunk_key] = {'pos': (x1, y1),
				'ground': [],
				'life': 0,
				'items': [],
				'neighbors': [],
				'digest': None}
			
			_tiles = {}
			for y2 in range(y1, y1+SETTINGS['chunk size']):
				for x2 in range(x1, x1+SETTINGS['chunk size']):
					if not source_map[x2][y2][2]:
						continue
					
					_chunk_map[_chunk_key]['ground'].append((x2, y2))
					_tile_id = source_map[x2][y2][2]['id']
					
					if _tile_id in [tile['id'] for tile in CONCRETE_TILES]:
						_type = 'road'
					elif _tile_id == WALL_TILE['id'] or _tile_id in [tile['id'] for tile in CONCRETE_FLOOR_TILES]:
						_type = 'wall'
					elif _tile_id in [tile['id'] for tile in DIRT_TILES]:
						_type = 'dirt'
					else:
						_type = 'other'
					
					if _type in _tiles:
						_tiles[_type] += 1
					else:
						_tiles[_type] = 1
			
			_total_tiles = sum(_tiles.values())
			for tile in _tiles.keys():
				_tiles[tile] = (_tiles[tile]/float(_total_tiles))*100
			
			if 'wall' in _tiles and _tiles['wall']>=15:
				_chunk_map[_chunk_key]['type'] = 'building'
			elif 'road' in _tiles and _tiles['road']>=15:
				_chunk_map[_chunk_key]['type'] = 'road'
			else:
				_chunk_map[_chunk_key]['type'] = 'other'
	
	CHUNK_MAP.update(_chunk_map)
	logging.info('Chunk map updated in %.2f seconds.' % (time.time()-_stime))
			
def smooth_chunk_map():
	_stime = time.time()
	_runs = 0
	_chunk_map = copy.deepcopy(CHUNK_MAP)
	_change = True
	
	while _change:
		_change = False
		_runs += 1
		
		for y1 in range(0, MAP_SIZE[1], SETTINGS['chunk size']):
			for x1 in range(0, MAP_SIZE[0], SETTINGS['chunk size']):
				_current_chunk_key = '%s,%s' % (x1, y1)
				_current_chunk = _chunk_map[_current_chunk_key]
				_neighbors = []
				
				for pos in [(-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)]:
					x2 = x1+(pos[0]*SETTINGS['chunk size'])
					y2 = y1+(pos[1]*SETTINGS['chunk size'])
					
					if x2>=MAP_SIZE[0] or x2<0 or y2>=MAP_SIZE[1] or y2<0:
						continue
					
					_neighbor_chunk_key = '%s,%s' % (x2, y2)
					_neighbor_chunk = _chunk_map[_neighbor_chunk_key]
					_neighbors.append(_neighbor_chunk_key)
				
				for _neighbor_chunk_key in _neighbors:
					_neighbor_chunk = _chunk_map[_neighbor_chunk_key]
					
					if _current_chunk['type'] == _neighbor_chunk['type']:
						if not _neighbor_chunk_key in _current_chunk['neighbors']:
							_current_chunk['neighbors'].append(_neighbor_chunk_key)
							_change = True
				
				_chunk_map[_current_chunk_key] = _current_chunk
	
	CHUNK_MAP.update(_chunk_map)	
	logging.info('Chunk map smoothing completed in %.2f seconds (%s runs).' % (time.time()-_stime, _runs))

def find_all_linked_chunks(chunk_key, check=[]):
	_linked_chunks = []
	_unchecked_chunks = [chunk_key]
	
	_check = []
	for _entry in check:
		_check.extend(_entry)
	
	if chunk_key in _check:
		return []
	
	while _unchecked_chunks:
		_current_chunk_key = _unchecked_chunks.pop()
		_linked_chunks.append(_current_chunk_key)
		_current_chunk = get_chunk(_current_chunk_key)
		
		for neighbor_chunk_key in _current_chunk['neighbors']:
			if neighbor_chunk_key in _unchecked_chunks or neighbor_chunk_key in _linked_chunks or neighbor_chunk_key in _check:
				continue
			
			_neighbor_chunk = get_chunk(neighbor_chunk_key)
			
			if not _neighbor_chunk['type'] == _current_chunk['type']:
				continue
			
			_unchecked_chunks.append(neighbor_chunk_key)
	
	return _linked_chunks

def generate_reference_maps():
	_stime = time.time()
	
	for y1 in range(0, MAP_SIZE[1], SETTINGS['chunk size']):
		for x1 in range(0, MAP_SIZE[0], SETTINGS['chunk size']):
			_current_chunk_key = '%s,%s' % (x1, y1)
			_current_chunk = get_chunk(_current_chunk_key)
			
			if _current_chunk['type'] == 'road':
				_ret = find_all_linked_chunks(_current_chunk_key, check=REFERENCE_MAP['roads'])
				if _ret:
					REFERENCE_MAP['roads'].append(_ret)
			elif _current_chunk['type'] == 'building':
				_ret = find_all_linked_chunks(_current_chunk_key, check=REFERENCE_MAP['buildings'])
				if _ret:
					REFERENCE_MAP['buildings'].append(_ret)
	
	logging.info('Reference map created in %.2f seconds.' % (time.time()-_stime))
	logging.info('\tRoads:\t\t %s' % (len(REFERENCE_MAP['roads'])))
	logging.info('\tBuildings:\t %s' % (len(REFERENCE_MAP['buildings'])))
