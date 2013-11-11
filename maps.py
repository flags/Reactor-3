from globals import *
from tiles import *

import graphics as gfx
import life as lfe

import maputils
import numbers
import drawing
import effects
import weather
import logic
import items
import zones
import alife
import tiles

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

def create_map(size=MAP_SIZE):
	_map = []

	for x in range(size[0]):
		_y = []
		for y in range(size[1]):
			_z = []
			for z in range(size[2]):
				if z == 2:
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

def save_map(map_name, base_dir=DATA_DIR):
	_map_dir = os.path.join(base_dir,'maps')
	if not map_name.count('.dat'):
		map_name+='.dat'

	try:
		os.mkdir(_map_dir)
	except:
		pass
		
	for light in WORLD_INFO['lights']:
		if 'los' in light:
			del light['los']
		
		if 'old_pos' in light:
			del light['old_pos']

	#For debug
	#for key in WORLD_INFO:
	#	print key
	#	json.dumps(WORLD_INFO[key])
	#for item in WORLD_INFO['items']:
	#	print item
	#	print WORLD_INFO['items'][item]
	#	json.dumps(WORLD_INFO['items'][item])

	with open(os.path.join(_map_dir,map_name), 'w') as _map_file:
		try:
			_map = WORLD_INFO['map']
			_slices = WORLD_INFO['slices']
			_chunk_map = WORLD_INFO['chunk_map']
			
			del WORLD_INFO['map']
			del WORLD_INFO['slices']
			del WORLD_INFO['chunk_map']
			
			_weather_light_map = None
			if 'light_map' in WORLD_INFO['weather']:
				_weather_light_map = WORLD_INFO['weather']['light_map']
				del WORLD_INFO['weather']['light_map']
			
			_map_file.write('world_info:%s\n' % json.dumps(WORLD_INFO))
			
			for _slice in _slices.keys():
				if '_map' in _slices[_slice]:
					del _slices[_slice]['_map']
				
				_map_file.write('slice:%s:%s\n' % (_slice, json.dumps(_slices[_slice])))
			
			for _chunk_key in _chunk_map:
				_map_file.write('chunk:%s:%s\n' % (_chunk_key, json.dumps(_chunk_map[_chunk_key])))
			
			logging.debug('Writing map to disk...')
			for x in range(MAP_SIZE[0]):
				_map_file.write('map:%s:%s\n' % (x, json.dumps(_map[x])))
				logging.debug('Wrote segment %s/%s' % (x+1, MAP_SIZE[0]))
			
			logging.info('Map \'%s\' saved to disk.' % map_name)			
			
			WORLD_INFO['map'] = _map
			WORLD_INFO['slices'] = _slices
			WORLD_INFO['chunk_map'] = _chunk_map
			
			if _weather_light_map:
				WORLD_INFO['weather']['light_map'] = _weather_light_map
				print WORLD_INFO['weather']
			
			logging.debug('Reloading slices...')
			reload_slices()
			logging.debug('Done!')
			
			logging.info('Map \'%s\' saved.' % map_name)
			gfx.log('Map \'%s\' saved.' % map_name)
		except TypeError as e:
			logging.critical('FATAL: Map not JSON serializable.')
			gfx.log('TypeError: Failed to save map (Map not JSON serializable).')
			
			raise e

def load_map(map_name, base_dir=DATA_DIR, like_new=False):
	_map_dir = os.path.join(base_dir,'maps')
	if not map_name.count('.dat'):
		map_name+='.dat'

	with open(os.path.join(_map_dir,map_name),'r') as _map_file:
		#try:
		#WORLD_INFO.update(json.loads(' '.join(_map_file.readlines())))
		for line in _map_file.readlines():
			line = line.rstrip()
			value = line.split(':')
			
			if line.startswith('chunk'):
				WORLD_INFO['chunk_map'][value[1]] = json.loads(':'.join(value[2:]))
			elif line.startswith('map'):
				WORLD_INFO['map'].append(json.loads(':'.join(value[2:])))
			elif line.startswith('slice'):
				WORLD_INFO['slices'][value[1]] = json.loads(':'.join(value[2:]))
			elif line.startswith('world_info'):
				WORLD_INFO.update(json.loads(':'.join(value[1:])))
		
		if 'items' in WORLD_INFO:
			ITEMS.update(WORLD_INFO['items'])
				
		#if not (x, y) in zone['map']:
		#for slice 
		
		_map_size = maputils.get_map_size(WORLD_INFO['map'])
		MAP_SIZE[0] = _map_size[0]
		MAP_SIZE[1] = _map_size[1]
		MAP_SIZE[2] = _map_size[2]
		
		reload_slices()
		
		if like_new:
			update_chunk_map()
			smooth_chunk_map()
		else:
			WORLD_INFO['chunk_map'].update(WORLD_INFO['chunk_map'])
		
		if WORLD_INFO['weather']:
			weather.create_light_map(WORLD_INFO['weather'])
		
		if not WORLD_INFO['lights']:
			logging.warning('World has no lights. Creating one manually.')
			effects.create_light((MAP_SIZE[0]/2, MAP_SIZE[1]/2, MAP_SIZE[2]-2), (255, 255, 255), 1, 0)
		#except Exception as e:
		#	raise e
		
		_map_size = maputils.get_map_size(WORLD_INFO['map'])
		
		for x in range(MAP_SIZE[0]):
			for y in range(MAP_SIZE[1]):
				for z in range(MAP_SIZE[2]):
					if not WORLD_INFO['map'][x][y][z]:
						continue
					
					for key in TILE_STRUCT_DEP:
						if key in WORLD_INFO['map'][x][y][z]:
							del WORLD_INFO['map'][x][y][z][key]
					
					for key in TILE_STRUCT:
						if not key in WORLD_INFO['map'][x][y][z]:
							WORLD_INFO['map'][x][y][z][key] = copy.copy(TILE_STRUCT[key])
		
		zones.cache_zones()
		create_position_maps()
		logging.info('Map \'%s\' loaded.' % map_name)
		gfx.log('Map \'%s\' loaded.' % map_name)

		return True
		#except TypeError:
		#	logging.error('FATAL: Map not JSON serializable.')
		#	gfx.log('TypeError: Failed to save map (Map not JSON serializable).')

def get_tile(pos):
	if WORLD_INFO['map'][pos[0]][pos[1]][pos[2]]:
		return True
	
	return False

def is_solid(pos):
	if not WORLD_INFO['map'][pos[0]][pos[1]][pos[2]]:
		return False
	
	if 'not_solid' in tiles.get_raw_tile(WORLD_INFO['map'][pos[0]][pos[1]][pos[2]]):
		return False
	
	return True

def position_is_in_map(pos):
	if pos[0] >= 0 and pos[0] <= MAP_SIZE[0]-1 and pos[1] >= 0 and pos[1] <= MAP_SIZE[1]-1:
		return True
	
	return False

def reset_lights():
	RGB_LIGHT_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	RGB_LIGHT_BUFFER[1] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	RGB_LIGHT_BUFFER[2] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))

def render_lights(source_map):
	if not SETTINGS['draw lights']:
		return False

	reset_lights()
	SUN = weather.get_lighting()
	
	#Not entirely my code. Made some changes to someone's code from libtcod's Python forum.
	RGB_LIGHT_BUFFER[0] = numpy.add(RGB_LIGHT_BUFFER[0], SUN[0])
	RGB_LIGHT_BUFFER[1] = numpy.add(RGB_LIGHT_BUFFER[1], SUN[1])
	RGB_LIGHT_BUFFER[2] = numpy.add(RGB_LIGHT_BUFFER[2], SUN[2])
	(x, y) = SETTINGS['light mesh grid']

	_remove_lights = []
	for light in WORLD_INFO['lights']:
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
		_x = numbers.clip(light['pos'][0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0])
		_y = numbers.clip(light['pos'][1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1])
		_top_left = (_x,_y,light['pos'][2])
		
		#TODO: Render only on move
		if not tuple(light['pos']) == tuple(light['old_pos']):
			light['los'] = cython_render_los.render_los(source_map, (light['pos'][0],light['pos'][1]), light['brightness']*2, top_left=_top_left)
		
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
		#brightness = numpy.clip(brightness * 255.0, 0, 255)
		brightness *= los
		brightness *= LOS_BUFFER[0]
		
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
		
		if logic.can_tick():
			if light['fade']:
				light['brightness'] -= light['fade']
			
			if light['brightness'] <= 0:
				_remove_lights.append(light)
	
	for light in _remove_lights:
		effects.delete_light(light)

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
	if cython:
		return cython_render_los.render_los(map, pos, size, life=life)
	else:
		return render_los(map,pos)

def render_los(map,position,los_buffer=LOS_BUFFER[0]):
	los_buffer = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	
	for pos1 in drawing.draw_circle(position, SETTINGS['los']):

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
	_map = []
	
	for x in range(0, MAP_SIZE[0]):
		_y = []
		
		for y in range(0, MAP_SIZE[1]):
			_y.append([])
		
		_map.append(_y)
	
	EFFECT_MAP.extend(copy.deepcopy(_map))
	LIFE_MAP.extend(copy.deepcopy(_map))
	
	logging.debug('Position maps created.')

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
			
			if not WORLD_INFO['map'][_x][_y][pos[2]] or WORLD_INFO['map'][_x][_y][pos[2]+1]:
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
			_chunk_map[_chunk_key] = {'pos': (x1, y1),
				'ground': [],
				'life': [],
				'items': [],
				'control': {},
				'neighbors': [],
				'flags': {},
				'reference': None,
				'last_updated': None,
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
			
			_total_tiles = sum(_tiles.values())
			for tile in _tiles.keys():
				_tiles[tile] = (_tiles[tile]/float(_total_tiles))*100
			
			if 'building' in _tiles:# and _tiles['building']>=9:
				_chunk_map[_chunk_key]['type'] = 'building'
			elif 'road' in _tiles and _tiles['road']>=15:
				_chunk_map[_chunk_key]['type'] = 'road'
			else:
				_chunk_map[_chunk_key]['type'] = 'other'
	
	WORLD_INFO['chunk_map'].update(_chunk_map)
	logging.info('Chunk map updated in %.2f seconds.' % (time.time()-_stime))
			
def smooth_chunk_map():
	_stime = time.time()
	_runs = 0
	_chunk_map = copy.deepcopy(WORLD_INFO['chunk_map'])
	_change = True
	
	while _change:
		_change = False
		_runs += 1
		
		for y1 in range(0, MAP_SIZE[1], WORLD_INFO['chunk_size']):
			for x1 in range(0, MAP_SIZE[0], WORLD_INFO['chunk_size']):
				_current_chunk_key = '%s,%s' % (x1, y1)
				_current_chunk = _chunk_map[_current_chunk_key]
				_neighbors = []
				
				for pos in [(-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)]:
					x2 = x1+(pos[0]*WORLD_INFO['chunk_size'])
					y2 = y1+(pos[1]*WORLD_INFO['chunk_size'])
					
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
	
	WORLD_INFO['chunk_map'].update(_chunk_map)	
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
	WORLD_INFO['references'] = {}
	WORLD_INFO['reference_map']['roads'] = []
	WORLD_INFO['reference_map']['buildings'] = []
	_ref_id = 1
	
	for y1 in range(0, MAP_SIZE[1], WORLD_INFO['chunk_size']):
		for x1 in range(0, MAP_SIZE[0], WORLD_INFO['chunk_size']):
			_current_chunk_key = '%s,%s' % (x1, y1)
			_current_chunk = get_chunk(_current_chunk_key)
			
			if _current_chunk['reference']:
				continue
			
			if _current_chunk['type'] == 'road':
				_ret = find_all_linked_chunks(_current_chunk_key)
				if _ret:
					WORLD_INFO['references'][str(_ref_id)] = _ret
					WORLD_INFO['reference_map']['roads'].append(str(_ref_id))
					
					for _chunk_key in _ret:
						get_chunk(_chunk_key)['reference'] = str(_ref_id)
			elif _current_chunk['type'] == 'building':
				_ret = find_all_linked_chunks(_current_chunk_key)
				if _ret:
					WORLD_INFO['references'][str(_ref_id)] = _ret
					WORLD_INFO['reference_map']['buildings'].append(str(_ref_id))
					
					for _chunk_key in _ret:
						get_chunk(_chunk_key)['reference'] = str(_ref_id)
			
			_ref_id += 1
	
	logging.debug('Reference map created in %.2f seconds.' % (time.time()-_stime))
	logging.debug('\tRoads:\t\t %s' % (len(WORLD_INFO['reference_map']['roads'])))
	logging.debug('\tBuildings:\t %s' % (len(WORLD_INFO['reference_map']['buildings'])))
	logging.debug('\tTotal:\t %s' % len(WORLD_INFO['references']))
