from globals import *
from tiles import *

import graphics as gfx
import life as lfe

import maputils
import numbers
import drawing
import effects
import weather
import mapgen
import logic
import items
import zones
import alife
import tiles
import fov

import logging
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

def create_map(size=MAP_SIZE, blank=False):
	_map = []

	for x in range(size[0]):
		_y = []
		for y in range(size[1]):
			_z = []
			for z in range(size[2]):
				if z == 2 and not blank:
					_z.append(create_tile(random.choice([TALL_GRASS_TILE,SHORT_GRASS_TILE,GRASS_TILE])))
				else:
					_z.append(None)

			_y.append(_z)
		_map.append(_y)

	logging.debug('Created new map of size (%s,%s).' % (size[0], size[1]))
	return _map

def reload_slices():
	for _slice in WORLD_INFO['slices'].values():
		#logging.debug('Loading slice: %s' % _slice['id'])
		
		_size = [_slice['bot_right'][0]-_slice['top_left'][0], _slice['bot_right'][1]-_slice['top_left'][1]]		
		_size[0] = numbers.clip(_size[0], 1, MAP_SIZE[0])
		_size[1] = numbers.clip(_size[1], 1, MAP_SIZE[1])
			
		_slice['_map'] = zones.create_map_array(size=_size)
		
		for pos in _slice['map']:
			_xx = _slice['top_left'][0]+1
			_yy = _slice['top_left'][1]+1
			
			_slice['_map'][pos[0]-_xx][pos[1]-_yy] = 1

def save_map(map_name, base_dir=MAP_DIR, only_cached=True):
	_map_dir = os.path.join(base_dir, map_name)
	
	#if base_dir == DATA_DIR:
	#	_map_dir = os.path.join(_map_dir, map_name)

	try:
		os.makedirs(_map_dir)
	except:
		pass
		
	for light in WORLD_INFO['lights']:
		if 'los' in light:
			del light['los']
		
		if 'old_pos' in light:
			del light['old_pos']

	with open(os.path.join(_map_dir, 'world.meta'), 'w') as _map_file:
		try:
			_slices = WORLD_INFO['slices']
			_references = WORLD_INFO['references']
			_chunk_map = WORLD_INFO['chunk_map']
			_map = WORLD_INFO['map']
			_weather_light_map = None
			
			del WORLD_INFO['slices']
			del WORLD_INFO['chunk_map']
			del WORLD_INFO['references']
			del WORLD_INFO['map']
			
			WORLD_INFO['map_size'] = maputils.get_map_size(_map)
			
			if 'light_map' in WORLD_INFO['weather']:
				_weather_light_map = WORLD_INFO['weather']['light_map']
				
				del WORLD_INFO['weather']['light_map']
			
			logging.debug('Writing map metadata to disk...')
			
			_map_file.write('world_info:%s\n' % json.dumps(WORLD_INFO))
			
			for _slice in _slices.keys():
				if '_map' in _slices[_slice]:
					del _slices[_slice]['_map']
				
				_map_file.write('slice:%s:%s\n' % (_slice, json.dumps(_slices[_slice])))
			
			for _chunk_key in _chunk_map:
				_map_file.write('chunk:%s:%s\n' % (_chunk_key, json.dumps(_chunk_map[_chunk_key])))
			
			#_map_file.write('slice_map:%s' % json.dumps(_slice_map))
			
			WORLD_INFO['slices'] = _slices
			WORLD_INFO['chunk_map'] = _chunk_map
			WORLD_INFO['references'] = _references
			WORLD_INFO['map'] = _map
			#WORLD_INFO['slice_map'] = _slice_map
			
			if _weather_light_map:
				WORLD_INFO['weather']['light_map'] = _weather_light_map
			
			#logging.debug('Reloading slices...')
			#reload_slices()
			#logging.debug('Done!')
			
		except TypeError as e:
			logging.critical('FATAL: Map not JSON serializable.')
			gfx.log('TypeError: Failed to save map (Map not JSON serializable).')
			
			raise e
		
	_chunk_cluster_size = WORLD_INFO['chunk_size']*10
	_map = WORLD_INFO['map']
	
	del WORLD_INFO['map']
	
	if only_cached:
		_cluster_keys = LOADED_CHUNKS
	else:
		_cluster_keys = []
		
		for y1 in range(0, MAP_SIZE[1], _chunk_cluster_size):
			for x1 in range(0, MAP_SIZE[0], _chunk_cluster_size):
				_cluster_keys.append('%s,%s' % (x1, y1))
				
	for cluster_key in _cluster_keys:
		_x1 = int(cluster_key.split(',')[0])
		_y1 = int(cluster_key.split(',')[1])
		
		with open(os.path.join(_map_dir, 'world_%s.cluster' % cluster_key.replace(',', '_')), 'w') as _cluster_file:
			for y2 in range(_y1, _y1+_chunk_cluster_size):
				for x2 in range(_x1, _x1+_chunk_cluster_size):
					_cluster_file.write(json.dumps(_map[x2][y2])+'\n')
	
	WORLD_INFO['map'] = _map
	SETTINGS['base_dir'] = _map_dir
	
def load_map(map_name, base_dir=MAP_DIR, cache_map=False):
	_map_dir = os.path.join(base_dir, map_name)

	WORLD_INFO['map'] = []

	with open(os.path.join(_map_dir, 'world.meta'),'r') as _map_file:
		for line in _map_file.readlines():
			line = line.rstrip()
			value = line.split(':')
			
			if line.startswith('chunk'):
				WORLD_INFO['chunk_map'][value[1]] = json.loads(':'.join(value[2:]))
			#elif line.startswith('slice_map'):
			#	WORLD_INFO['slice_map'] = json.loads(':'.join(value[1:]))
			elif line.startswith('slice'):
				WORLD_INFO['slices'][value[1]] = json.loads(':'.join(value[2:]))
			elif line.startswith('world_info'):
				WORLD_INFO.update(json.loads(':'.join(value[1:])))
		
		if 'items' in WORLD_INFO:
			ITEMS.update(WORLD_INFO['items'])
		
		MAP_SIZE[0] = WORLD_INFO['map_size'][0]
		MAP_SIZE[1] = WORLD_INFO['map_size'][1]
		MAP_SIZE[2] = WORLD_INFO['map_size'][2]
		
		WORLD_INFO['chunk_map'].update(WORLD_INFO['chunk_map'])
		
		if WORLD_INFO['weather']:
			weather.create_light_map(WORLD_INFO['weather'])
	
	logging.debug('Caching zones...')
	zones.cache_zones()
	logging.debug('Done!')
	
	logging.debug('Creating position maps...')
	create_position_maps()
	logging.debug('Done!')
	
	logging.debug('Reloading references...')
	reload_reference_maps()
	logging.debug('Done!')
	
	WORLD_INFO['map'] = create_map(blank=True)
	SETTINGS['base_dir'] = _map_dir
	
	if cache_map:
		cache_all_clusters()
	
	logging.info('Map \'%s\' loaded.' % map_name)
	gfx.log('Map \'%s\' loaded.' % map_name)

def load_cluster(cluster_key, base_dir=DATA_DIR):
	logging.debug('Loading cluster: %s' % cluster_key)
	LOADED_CHUNKS.append(cluster_key)
	
	_map_dir = base_dir
	_cluster_key = cluster_key
	_x1 = int(_cluster_key.split(',')[0])
	_y1 = int(_cluster_key.split(',')[1])
	_xc = 0
	
	_chunk_cluster_size = WORLD_INFO['chunk_size']*10
	
	with open(os.path.join(_map_dir, 'world_%s.cluster' % _cluster_key.replace(',', '_')), 'r') as _cluster_file:
		for line in _cluster_file.readlines():
			_sline = line.rstrip()
			
			if not _sline:
				continue
			
			WORLD_INFO['map'][_x1][_y1] = json.loads(_sline)
			
			if _xc<_chunk_cluster_size-1:
				_x1 += 1
				_xc += 1
			else:
				_xc = 0
				_x1 = int(_cluster_key.split(',')[0])
				_y1 += 1

def cache_all_clusters():
	_chunk_cluster_size = WORLD_INFO['chunk_size']*10
		
	for y1 in range(0, MAP_SIZE[1], _chunk_cluster_size):
		for x1 in range(0, MAP_SIZE[0], _chunk_cluster_size):
			_cluster_key = '%s,%s' % (x1, y1)
			
			load_cluster(_cluster_key, base_dir=SETTINGS['base_dir'])

def load_cluster_at_position_if_needed(position):
	if not 'base_dir' in SETTINGS:
		return False
	
	_chunk_cluster_size = WORLD_INFO['chunk_size']*10
	
	_cluster_key = '%s,%s' % ((position[0]/_chunk_cluster_size)*_chunk_cluster_size,
	                          (position[1]/_chunk_cluster_size)*_chunk_cluster_size)
	
	if _cluster_key == '0,0':
		raise Exception('d')
	
	if _cluster_key in LOADED_CHUNKS:
		return False
	
	load_cluster(_cluster_key, base_dir=SETTINGS['base_dir'])
	
	return True

def reload_reference_maps():
	WORLD_INFO['references'] = {}
	
	for chunk_key in WORLD_INFO['chunk_map']:
		if not 'reference' in WORLD_INFO['chunk_map'][chunk_key]:
			continue
		
		_ref_id = WORLD_INFO['chunk_map'][chunk_key]['reference']
		
		if _ref_id in WORLD_INFO['references']:
			WORLD_INFO['references'][_ref_id].append(chunk_key)
		else:
			WORLD_INFO['references'][_ref_id] = [chunk_key]

def get_tile(pos):
	if WORLD_INFO['map'][pos[0]][pos[1]][pos[2]]:
		return True
	
	return False

def is_solid(pos, source_map=None):
	if not source_map:
		source_map = WORLD_INFO['map']
	
	if not source_map[pos[0]][pos[1]][pos[2]]:
		return False
	
	_raw_tile = tiles.get_raw_tile(source_map[pos[0]][pos[1]][pos[2]])
	if 'not_solid' in _raw_tile and _raw_tile['not_solid']:
		return False
	
	return True

def is_oob(pos):
	return pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1] or pos[2]<0 or pos[2]>=MAP_SIZE[2]

def position_is_in_map(pos):
	if pos[0] >= 0 and pos[0] <= MAP_SIZE[0]-1 and pos[1] >= 0 and pos[1] <= MAP_SIZE[1]-1:
		return True
	
	return False

def reset_lights(size=MAP_WINDOW_SIZE):
	RGB_LIGHT_BUFFER[0] = numpy.zeros((size[1], size[0]))
	RGB_LIGHT_BUFFER[1] = numpy.zeros((size[1], size[0]))
	RGB_LIGHT_BUFFER[2] = numpy.zeros((size[1], size[0]))
	
	while REFRESH_POSITIONS:
		_pos = REFRESH_POSITIONS.pop()
		gfx.refresh_view_position(_pos[0], _pos[1], 'map')

def render_lights(size=MAP_WINDOW_SIZE, show_weather=True):
	if not SETTINGS['draw lights']:
		return False

	reset_lights(size=size)
	_weather_light = weather.get_lighting()
	
	#Not entirely my code. Made some changes to someone's code from libtcod's Python forum.
	RGB_LIGHT_BUFFER[0] = numpy.add(RGB_LIGHT_BUFFER[0], _weather_light[0])
	RGB_LIGHT_BUFFER[1] = numpy.add(RGB_LIGHT_BUFFER[1], _weather_light[1])
	RGB_LIGHT_BUFFER[2] = numpy.add(RGB_LIGHT_BUFFER[2], _weather_light[2])
	(x, y) = SETTINGS['light mesh grid']
	
	if show_weather:
		weather.generate_effects(size)

	_remove_lights = []
	for light in WORLD_INFO['lights']:
		_x_range = light['pos'][0]-CAMERA_POS[0]
		_y_range = light['pos'][1]-CAMERA_POS[1]
		
		if _x_range <= -20 or _x_range>=size[0]+20:
			continue
		
		if _y_range <= -20 or _y_range>=size[1]+20:
			continue
		
		if not 'old_pos' in light:
			light['old_pos'] = (0, 0, -2)
		else:
			light['old_pos'] = light['pos'][:]
		
		if 'follow_item' in light:
			if not light['follow_item'] in ITEMS:
				_remove_lights.append(light)
				continue
				
			light['pos'] = items.get_pos(light['follow_item'])[:]
		
		_render_x = light['pos'][0]-CAMERA_POS[0]
		_render_y = light['pos'][1]-CAMERA_POS[1]
		_x = numbers.clip(light['pos'][0]-(size[0]/2),0,MAP_SIZE[0])
		_y = numbers.clip(light['pos'][1]-(size[1]/2),0,MAP_SIZE[1])
		_top_left = (_x,_y,light['pos'][2])
		
		#TODO: Render only on move
		if not tuple(light['pos']) == tuple(light['old_pos']):
			light['los'] = cython_render_los.render_los((light['pos'][0],light['pos'][1]), light['brightness']*2, view_size=size, top_left=_top_left)
		
		los = light['los'].copy()
		
		_x_scroll = _x-CAMERA_POS[0]
		_x_scroll_over = 0
		_y_scroll = _y-CAMERA_POS[1]
		_y_scroll_over = 0
		
		if _x_scroll<0:
			_x_scroll_over = _x_scroll
			_x_scroll = los.shape[1]+_x_scroll
		
		if _y_scroll<0:
			_y_scroll_over = _y_scroll
			_y_scroll = los.shape[0]+_y_scroll
		
		los = numpy.roll(los, _y_scroll, axis=0)
		los = numpy.roll(los, _x_scroll, axis=1)
		los[_y_scroll_over:_y_scroll,] = 1
		los[:,_x_scroll_over:_x_scroll] = 1
		
		if SETTINGS['diffuse light']:
			_y, _x = diffuse_light((y, x))
			(x, y) = numpy.meshgrid(_x, _y)
		
		sqr_distance = (x - (_render_x))**2.0 + (y - (_render_y))**2.0
		
		brightness = numbers.clip(random.uniform(light['brightness']*light['shake'], light['brightness']), 0.01, 50) / sqr_distance
		brightness *= los
		#brightness *= LOS_BUFFER[0]
		
		#_mod = (abs((WORLD_INFO['length_of_day']/2)-WORLD_INFO['real_time_of_day'])/float(WORLD_INFO['length_of_day']))*5.0	
		#_mod = numbers.clip(_mod-1, 0, 1)
		#(255*_mod, 165*_mod, 0*_mod)
		#print brightness
		#light['brightness'] = 25
		#light['color'][0] = 255*(light['brightness']/255.0)
		#light['color'][1] = (light['brightness']/255.0)
		#light['color'][2] = 255*(light['brightness']/255.0)
		RGB_LIGHT_BUFFER[0] -= (brightness.clip(0, 2)*(light['color'][0]))#numpy.subtract(RGB_LIGHT_BUFFER[0], light['color'][0]).clip(0, 255)
		RGB_LIGHT_BUFFER[1] -= (brightness.clip(0, 2)*(light['color'][1]))#numpy.subtract(RGB_LIGHT_BUFFER[1], light['color'][1]).clip(0, 255)
		RGB_LIGHT_BUFFER[2] -= (brightness.clip(0, 2)*(light['color'][2]))#numpy.subtract(RGB_LIGHT_BUFFER[2], light['color'][2]).clip(0, 255)
		
		#RGB_LIGHT_BUFFER[0] *= LOS_BUFFER[0]
		#RGB_LIGHT_BUFFER[1] *= LOS_BUFFER[0]
		#RGB_LIGHT_BUFFER[2] *= LOS_BUFFER[0]

def diffuse_light(source_light):
	light = source_light[0]+source_light[1]
	
	for i in range(1):
		_light = light.copy()
		
		for x in range(1, light.shape[1]-1):
			for y in range(1, light.shape[0]-1):
				#if light[y, x]:
				#	continue
				
				#print light[y, x]
				_brightness = 0
				for pos in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
					_brightness += light[y+pos[1], x+pos[0]]
				
				_light[y, x] = _brightness/8.0
				#print light[y, x],_brightness/5.0
		
		light = _light
	
	return (light.ravel(1), light.ravel(0))

def _render_los(map, pos, size, cython=False, life=None):
	#LOS times:
	#Raycast: 0.0453310012817
	#Recursive Shadowcasting: 0.0119090080261 (worst case), 0.000200033187866 (best case)
	
	_start_time = time.time()
	_fov = fov.fov(pos, size)
	print time.time()-_start_time
	
	return _fov

def render_map_slices():
	SETTINGS['map_slices'] = []
	
	for z in range(0, MAP_SIZE[2]):
		SETTINGS['map_slices'].append(tcod.console_new(MAP_SIZE[0], MAP_SIZE[1]))
		for x in range(0, MAP_SIZE[0]):
			for y in range(0, MAP_SIZE[1]):
				if not WORLD_INFO['map'][x][y][z]:
					continue
				
				gfx.blit_tile_to_console(SETTINGS['map_slices'][z], x, y, WORLD_INFO['map'][x][y][z])

def fast_draw_map():
	_CAM_X = numbers.clip(CAMERA_POS[0], 0, MAP_SIZE[0]-MAP_WINDOW_SIZE[0])
	_CAM_Y = numbers.clip(CAMERA_POS[1], 0, MAP_SIZE[1]-MAP_WINDOW_SIZE[1])
	
	tcod.console_blit(SETTINGS['map_slices'][2], _CAM_X, _CAM_Y, MAP_WINDOW_SIZE[0], MAP_WINDOW_SIZE[1], MAP_WINDOW, 0, 0)

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
				'map')

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
	return WORLD_INFO['chunk_map'][chunk_id]

def enter_chunk(chunk_key, life_id):
	chunk = get_chunk(chunk_key)
    
	if not life_id in chunk['life']:
		chunk['life'].append(life_id)

def leave_chunk(chunk_key, life_id):
	chunk = get_chunk(chunk_key)
    
	if life_id in chunk['life']:
		chunk['life'].remove(life_id)

def get_open_position_in_chunk(source_map, chunk_id):
	_chunk = get_chunk(chunk_id)
	
	for x1 in range(WORLD_INFO['chunk_size']):
		x = x1+_chunk['pos'][0]
		
		for y1 in range(WORLD_INFO['chunk_size']):
			y = y1+_chunk['pos'][1]
			
			if source_map[x][y][2] and not source_map[x][y][3]:
				return (x, y)
	
	return False

def create_position_maps():
	_emap = []
	_lmap = []
	
	for x in range(0, MAP_SIZE[0]):
		_ye = []
		_yl = []
		
		for y in range(0, MAP_SIZE[1]):
			_ye.append([])
			_yl.append([])
		
		_emap.append(_ye)
		_lmap.append(_yl)
	
	EFFECT_MAP.extend(_emap)
	LIFE_MAP.extend(_lmap)

def create_search_map(life, pos, size):
	_map = numpy.ones((size, size))
	
	_x_top_left = numbers.clip(pos[0]-(size/2), 0, MAP_SIZE[0])
	_y_top_left = numbers.clip(pos[1]-(size/2), 0, MAP_SIZE[1])
	
	for x in range(0, size):
		_x = _x_top_left+x
		
		if _x >= MAP_SIZE[0]-1:
			continue
		
		for y in range(0, size):
			_y = _y_top_left+y
			
			if _y >= MAP_SIZE[1]-1:
				continue
			
			if not is_solid((_x, _y, pos[2])) or is_solid((_x, _y, pos[2]+1)):
				_map[y, x] = 0
			else:
				_map[y, x] = alife.judgement.judge_search_pos(life, (_x, _y))
	
	return _map

def update_chunk_map():
	_stime = time.time()
	_chunk_map = {}
	
	for y1 in range(0, MAP_SIZE[1], WORLD_INFO['chunk_size']):
		for x1 in range(0, MAP_SIZE[0], WORLD_INFO['chunk_size']):
			_chunk_key = '%s,%s' % (x1, y1)
			_chunk_type = WORLD_INFO['chunk_map'][_chunk_key]['type']
			
			if _chunk_type == 'town':
				_chunk_type = 'building'
			
			_chunk_map[_chunk_key] = {'pos': (x1, y1),
				'ground': [],
				'life': [],
				'items': [],
				'control': {},
				'flags': WORLD_INFO['chunk_map'][_chunk_key]['flags'],
				'reference': WORLD_INFO['chunk_map'][_chunk_key]['reference'],
				'type': _chunk_type,
				'max_z': 0}
			
			_tiles = {}
			for y2 in range(y1, y1+WORLD_INFO['chunk_size']):
				for x2 in range(x1, x1+WORLD_INFO['chunk_size']):
					if not WORLD_INFO['map'][x2][y2][2]:
						continue
					
					if not WORLD_INFO['map'][x2][y2][3]:
						_chunk_map[_chunk_key]['ground'].append((x2, y2))
					
					_tile = get_raw_tile(WORLD_INFO['map'][x2][y2][2])
					
					if not _tile:
						continue
					
					for z in range(0, MAP_SIZE[2]):
						if WORLD_INFO['map'][x2][y2][z] and z>_chunk_map[_chunk_key]['max_z']:
							_chunk_map[_chunk_key]['max_z'] = z
					
					if 'type' in _tile:
						_type = _tile['type']
					else:
						_type = 'other'
					
					if _type in _tiles:
						_tiles[_type] += 1
					else:
						_tiles[_type] = 1
			
			#_total_tiles = sum(_tiles.values())
			#for tile in _tiles.keys():
				#_tiles[tile] = (_tiles[tile]/float(_total_tiles))*100
			
			#if 'building' in _tiles:# and _tiles['building']>=9:
				#_chunk_map[_chunk_key]['type'] = 'building'
			#elif 'road' in _tiles and _tiles['road']>=15:
				#_chunk_map[_chunk_key]['type'] = 'road'
			#else:
				#_chunk_map[_chunk_key]['type'] = 'other'
	
	WORLD_INFO['chunk_map'].update(_chunk_map)
	logging.info('Chunk map updated in %.2f seconds.' % (time.time()-_stime))

def draw_chunk_map(life=None, show_faction_ownership=False):
	_x_min = numbers.clip(CAMERA_POS[0]/WORLD_INFO['chunk_size'], 0, MAP_SIZE[0]/WORLD_INFO['chunk_size'])
	_y_min = numbers.clip(CAMERA_POS[1]/WORLD_INFO['chunk_size'], 0, MAP_SIZE[1]/WORLD_INFO['chunk_size'])
	_x_max = numbers.clip(_x_min+WINDOW_SIZE[0], 0, MAP_SIZE[0]/WORLD_INFO['chunk_size'])
	_y_max = numbers.clip(_y_min+WINDOW_SIZE[1], 0, MAP_SIZE[1]/WORLD_INFO['chunk_size'])
	
	_life_chunk_key = None
	
	if life:
		_life_chunk_key = lfe.get_current_chunk_id(life)
	
	for x in range(_x_min, _x_max):
		_d_x = x-(CAMERA_POS[0]/WORLD_INFO['chunk_size'])
		
		if 0>_d_x >= WINDOW_SIZE[0]:
			continue
		
		for y in range(_y_min, _y_max):
			_d_y = y-(CAMERA_POS[1]/WORLD_INFO['chunk_size'])
			_draw = True
			_fore_color = tcod.darker_gray
			_back_color = tcod.darkest_gray
			
			if 0>_d_y >= WINDOW_SIZE[1]:
				continue
			
			_chunk_key = '%s,%s' % (x*WORLD_INFO['chunk_size'], y*WORLD_INFO['chunk_size'])
			
			if life:
				if not _chunk_key in life['known_chunks']:
					_draw = False
			
			if _draw:
				_type = WORLD_INFO['chunk_map'][_chunk_key]['type']
				_char = 'x'
				
				if _type in ['building', 'town']:
					_fore_color = tcod.light_gray
					_char = 'B'
				elif _type in ['outpost', 'factory']:
					_fore_color = tcod.desaturated_green
					_back_color = tcod.desaturated_han
					_char = 'M'
				elif _type == 'field':
					_fore_color = tcod.yellow
				elif _type == 'forest':
					_fore_color = tcod.dark_green
				elif _type in ['road', 'driveway']:
					_fore_color = tcod.white
					_back_color = tcod.black
					_char = '.'
				
				if _chunk_key == _life_chunk_key and time.time()%1>=.5:
					_fore_color = tcod.white
					_char = 'X'
				
				gfx.blit_char_to_view(_d_x, _d_y, _char, (_fore_color, _back_color), 'chunk_map')
			else:
				gfx.blit_char_to_view(_d_x, _d_y, 'x', (tcod.darker_gray, tcod.darkest_gray), 'chunk_map')
