from globals import *
from tiles import *
import graphics as gfx
import maputils
import logging
import drawing
import random
import numpy
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

def render_lights():
	if not SETTINGS['draw lights']:
		return False

	reset_lights()
	RGB_LIGHT_BUFFER[0] = numpy.add(RGB_LIGHT_BUFFER[0], SUN_BRIGHTNESS[0])
	RGB_LIGHT_BUFFER[1] = numpy.add(RGB_LIGHT_BUFFER[1], SUN_BRIGHTNESS[0])
	RGB_LIGHT_BUFFER[2] = numpy.add(RGB_LIGHT_BUFFER[2], SUN_BRIGHTNESS[0])
	(x, y) = numpy.meshgrid(range(MAP_WINDOW_SIZE[0]), range(MAP_WINDOW_SIZE[1]))
	
	for light in LIGHTS:
		sqr_distance = (x - (light['x']-CAMERA_POS[0]))**2 + (y - (light['y']-CAMERA_POS[1]))**2
		
		brightness = light['brightness'] / sqr_distance
		brightness = numpy.clip(brightness * 255, 0, 255)
	
		RGB_LIGHT_BUFFER[0] = numpy.subtract(RGB_LIGHT_BUFFER[0],brightness).clip(0,255)
		RGB_LIGHT_BUFFER[1] = numpy.subtract(RGB_LIGHT_BUFFER[1],brightness).clip(0,255)
		RGB_LIGHT_BUFFER[2] = numpy.subtract(RGB_LIGHT_BUFFER[2],brightness).clip(0,255)

def _render_los(map,pos,cython=False):
	if cython:
		cython_render_los.render_los(map,pos)
	else:
		render_los(MAP,pos)

def render_los(map,position):
	LOS_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	
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
					LOS_BUFFER[0][_y,_x] = 1
					
					continue
				
			if _dark:
				continue

			LOS_BUFFER[0][_y,_x] = 1

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
		for z in range(MAP_SIZE[2]):
			if map[x][y][z]:
				_tile = map[x][y][z]
			else:
				_tile = BLANK_TILE
			
			gfx.blit_tile(_RENDER_X,
				MAP_SIZE[2]-z,
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
