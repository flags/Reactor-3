from globals import *
from tiles import *
import graphics as gfx
import logging
import random
import json
import os

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

def save_map(map):
	_map_dir = os.path.join(DATA_DIR,'maps')

	try:
		os.mkdir(_map_dir)
	except:
		pass

	with open(os.path.join(_map_dir,'map1.dat'),'w') as _map_file:
		try:
			_map_file.write(json.dumps(map))
			gfx.log('Map saved.')
		except TypeError:
			logging.error('FATAL: Map not JSON serializable.')
			gfx.log('TypeError: Failed to save map (Map not JSON serializable).')

def load_map(map_name):
	_map_dir = os.path.join(DATA_DIR,'maps')

	with open(os.path.join(_map_dir,map_name),'r') as _map_file:
		try:
			_map_string = json.loads(_map_file.readline())
			logging.info('Map \'%s\' loaded.' % map_name)
			gfx.log('Loaded map \'%s\' from disk.' % map_name)

			return _map_string
		except TypeError:
			logging.error('FATAL: Map not JSON serializable.')
			gfx.log('TypeError: Failed to save map (Map not JSON serializable).')

def render_map(map):
	_X_MAX = CAMERA_POS[0]+MAP_WINDOW_SIZE[0]
	_Y_MAX = CAMERA_POS[1]+MAP_WINDOW_SIZE[1]

	if _X_MAX>MAP_SIZE[0]:
		_X_MAX = MAP_SIZE[0]

	if _Y_MAX>MAP_SIZE[1]:
		_Y_MAX = MAP_SIZE[1]

	for x in range(CAMERA_POS[0],_X_MAX):
		_X_POS = x-CAMERA_POS[0]
		for y in range(CAMERA_POS[1],_Y_MAX):
			_Y_POS = y-CAMERA_POS[1]
			for z in range(MAP_SIZE[2]):
				if map[x][y][z]:
					if z > CAMERA_POS[2] and SETTINGS['draw z-levels above']:
						gfx.blit_tile(_X_POS,_Y_POS,map[x][y][z])
						gfx.lighten_tile(_X_POS,_Y_POS,abs((CAMERA_POS[2]-z))*30)
					elif z == CAMERA_POS[2]:
						gfx.blit_tile(_X_POS,_Y_POS,map[x][y][z])
						gfx.lighten_tile(_X_POS,_Y_POS,0)
						gfx.darken_tile(_X_POS,_Y_POS,0)
					elif z < CAMERA_POS[2] and SETTINGS['draw z-levels below']:
						gfx.blit_tile(_X_POS,_Y_POS,map[x][y][z])
						gfx.darken_tile(_X_POS,_Y_POS,abs((CAMERA_POS[2]-z))*30)

def flood_select_by_tile(map_array,tile,where):
	_to_check = [where]
	_checked = []
	_selected = []
	
	while _to_check:
		for _x in range(-1,2):
			for _y in range(-1,2):
				if not _x and not _y:
					continue
				
				x = _x+_to_check[0][0]
				y = _y+_to_check[0][1]
				z = _to_check[0][2]
				
				if map_array[x][y][z]['id'] == tile['id']:
					if not (x,y,z) in _selected:
						_selected.append((x,y,z))
					
					if not (x,y,z) in _to_check:
						_to_check.append((x,y,z))
		
		_to_check.pop(0)
	
	return _selected