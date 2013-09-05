#Tools for generating buildings (prefabs)
from globals import DATA_DIR
from tiles import *

import graphics as gfx

import logging
import random
import json
import os

def create_new_prefab(size):
	if not len(size) == 3:
		raise Exception('Invalid prefab size: Expected 3 arguments.')
	
	_prefab = []

	for x in range(size[0]):
		_y = []
		for y in range(size[1]):
			_z = []
			for z in range(size[2]):
				#if z==0:
				#	_z.append(create_tile(TALL_GRASS_TILE))
				#else:
				_z.append(None)

			_y.append(_z)
		_prefab.append(_y)

	logging.debug('Created new prefab of size (%s,%s,%s).' % (size[0],size[1],size[2]))
	
	return {'map': _prefab,'size': size}

def save(prefab):
	with open(os.path.join(PREFAB_DIR, 'test.json'), 'w') as f:
		f.write(json.dumps(prefab))

def draw_prefab(prefab):
	_X_MAX = PREFAB_CAMERA_POS[0]+PREFAB_WINDOW_SIZE[0]
	_Y_MAX = PREFAB_CAMERA_POS[1]+PREFAB_WINDOW_SIZE[1]
	
	#DARK_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], PREFAB_WINDOW_SIZE[0]))
	#LIGHT_BUFFER[0] = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	
	map = prefab['map']

	if _X_MAX>prefab['size'][0]:
		_X_MAX = prefab['size'][0]

	if _Y_MAX>prefab['size'][1]:
		_Y_MAX = prefab['size'][1]

	for x in range(PREFAB_CAMERA_POS[0],_X_MAX):
		_RENDER_X = x-PREFAB_CAMERA_POS[0]
		
		for y in range(PREFAB_CAMERA_POS[1],_Y_MAX):
			_RENDER_Y = y-PREFAB_CAMERA_POS[1]
			_drawn = False
			
			for z in range(prefab['size'][2]-1,-1,-1):
				if map[x][y][z]:
					gfx.blit_tile(_RENDER_X,
						_RENDER_Y,
						map[x][y][z],
						char_buffer=PREFAB_CHAR_BUFFER,
						rgb_fore_buffer=PREFAB_RGB_FORE_BUFFER,
						rgb_back_buffer=PREFAB_RGB_BACK_BUFFER)
					
					_drawn = True
					break
					#if z > PREFAB_CAMERA_POS[2] and SETTINGS['draw z-levels above']:
					#	gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
					#	gfx.darken_tile(_RENDER_X,_RENDER_Y,abs((PREFAB_CAMERA_POS[2]-z))*30)
					#	_drawn = True
					#elif z == PREFAB_CAMERA_POS[2]:
					#	if (x,y,z) in SELECTED_TILES[0] and time.time()%1>=0.5:
					#		gfx.blit_char(_RENDER_X,_RENDER_Y,'X',darker_grey,black)
					#	else:
					#		gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
					#	_drawn = True
					#elif z < PREFAB_CAMERA_POS[2] and SETTINGS['draw z-levels below']:
					#	gfx.blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z])
					#	gfx.darken_tile(_RENDER_X,_RENDER_Y,abs((PREFAB_CAMERA_POS[2]-z))*30)
					#	_drawn = True
				
					#if SETTINGS['draw z-levels above'] and _drawn:
					#	break
			
			if not _drawn:
				gfx.blit_tile(_RENDER_X,
					_RENDER_Y,
					BLANK_TILE,
					char_buffer=PREFAB_CHAR_BUFFER,
					rgb_fore_buffer=PREFAB_RGB_FORE_BUFFER,
					rgb_back_buffer=PREFAB_RGB_BACK_BUFFER)
