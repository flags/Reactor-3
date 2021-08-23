from graphics import blit_tile, darken_tile, blit_char, blit_tile, get_view_by_name, blit_char_to_view
from globals import MAP_CHAR_BUFFER, DARK_BUFFER
from tiles import *

import libtcodpy as tcod

import numbers
import effects
import numpy
import tiles
import alife

import time

VERSION = 6

def render_map(map, force_camera_pos=None, view_size=MAP_WINDOW_SIZE, **kwargs):
	cdef int _CAMERA_POS[2]
	cdef int _MAP_SIZE[2]
	cdef int _MAP_WINDOW_SIZE[2]
	_CAMERA_POS[0] = CAMERA_POS[0]
	_CAMERA_POS[1] = CAMERA_POS[1]
	_CAMERA_POS[2] = CAMERA_POS[2]
	_MAP_SIZE[0] = MAP_SIZE[0]
	_MAP_SIZE[1] = MAP_SIZE[1]
	_MAP_SIZE[2] = MAP_SIZE[2]
	_MAP_WINDOW_SIZE[0] = view_size[0]
	_MAP_WINDOW_SIZE[1] = view_size[1]
	
	cdef int x, y, z
	cdef int _X_MAX = _CAMERA_POS[0]+view_size[0]
	cdef int _Y_MAX = _CAMERA_POS[1]+view_size[1]
	cdef int _X_START = _CAMERA_POS[0]
	cdef int _Y_START = _CAMERA_POS[1]
	cdef int _RENDER_X = 0
	cdef int _RENDER_Y = 0
	
	cdef int _min_los_x = 0
	cdef int _max_los_x = view_size[0]
	cdef int _min_los_y = 0
	cdef int _max_los_y = view_size[1]
	
	cdef int _x_mod = 0
	cdef int _y_mod = 0
	
	if force_camera_pos:
		_cam_pos = force_camera_pos[:]
	else:
		_cam_pos = SETTINGS['camera_track'][:]
	
	if not CAMERA_POS[0]:
		_x_mod = SETTINGS['camera_track'][0]-view_size[0]//2
	elif CAMERA_POS[0]+view_size[0]>=MAP_SIZE[0]:
		_x_mod = 0
   
	if not CAMERA_POS[1]:
		_y_mod = SETTINGS['camera_track'][1]-view_size[1]//2
	elif CAMERA_POS[1]+view_size[1]>=MAP_SIZE[1]:
		_y_mod = 0
	
	_camera_x_offset = CAMERA_POS[0]-_cam_pos[0]
	_camera_y_offset = CAMERA_POS[1]-_cam_pos[1]
	
	los = None
	if 'los' in kwargs:
		los = kwargs['los']
		_min_los_x = (los.shape[0]//2)-view_size[0]//2-_x_mod+_camera_x_offset
		_max_los_x = los.shape[0]
		_min_los_y = (los.shape[1]//2)-view_size[1]//2-_y_mod+_camera_y_offset
		_max_los_y = los.shape[1]
	
	_view = get_view_by_name('map')
	_TEMP_MAP_CHAR_BUFFER = _view['char_buffer'][1].copy()

	if _X_MAX>_MAP_SIZE[0]:
		_X_MAX = _MAP_SIZE[0]

	if _Y_MAX>_MAP_SIZE[1]:
		_Y_MAX = _MAP_SIZE[1]

	for x in range(_X_START, _X_MAX):
		_RENDER_X = x-_CAMERA_POS[0]
		for y in range(_Y_START, _Y_MAX):
			_RENDER_Y = y-_CAMERA_POS[1]

			if _min_los_x+_RENDER_X<0 or _min_los_x+_RENDER_X>=_max_los_x or _min_los_y+_RENDER_Y<0 or _min_los_y+_RENDER_Y>=_max_los_y:
				_visible = False
			elif 'los' in kwargs:
				_visible = los[_min_los_x+_RENDER_X, _min_los_y+_RENDER_Y]
			else:
				_visible = True
			
			if _TEMP_MAP_CHAR_BUFFER[_RENDER_Y,_RENDER_X]:
				continue
			
			_view['light_buffer'][1][_RENDER_Y, _RENDER_X] = 0
			_drawn = False
			_shadow = 2
			for z in range(MAP_SIZE[2]-1,-1,-1):
				if map[x][y][z]:
					if z > _CAMERA_POS[2] and SETTINGS['draw z-levels above']:
						if 'translucent' in tiles.get_raw_tile(tiles.get_tile((x, y, z))):
							if _shadow >= 2:
								_shadow += 1
						else:
							_shadow = 0
						
						if not _visible:
							blit_tile(_RENDER_X, _RENDER_Y, map[x][y][z], 'map')
							darken_tile(_RENDER_X, _RENDER_Y, abs((_CAMERA_POS[2]-z))*10)
							_drawn = True
						
					elif z == _CAMERA_POS[2]:
						if (x,y,z) in SELECTED_TILES[0] and time.time()%1>=0.5:
							if time.time()%1>=0.75:
								_back_color = tcod.black
							else:
								_back_color = tcod.white
							
							blit_char_to_view(_RENDER_X,
										_RENDER_Y,
										'X',
										(tcod.darker_grey, _back_color),
										'map')
						else:
							if _shadow > 2:
								darken_tile(_RENDER_X, _RENDER_Y, 15*(_shadow-2))
							
							if map[x][y][z+1]:
								blit_tile(_RENDER_X, _RENDER_Y, map[x][y][z+1], 'map')
							else:
								blit_tile(_RENDER_X, _RENDER_Y, map[x][y][z], 'map')
							
							if SETTINGS['draw effects']:
								if _visible:
									effects.draw_splatter((x,y,z), (_RENDER_X,_RENDER_Y))
									effects.draw_effect((x, y))
			
						if not _visible:
							darken_tile(_RENDER_X, _RENDER_Y, 30)
						
						if SETTINGS['draw visible chunks']:
							_visible_chunks = alife.brain.get_flag(LIFE[SETTINGS['controlling']], 'visible_chunks')
							
							if _visible_chunks:
								for _chunk in _visible_chunks:
									if alife.chunks.position_is_in_chunk((x, y), _chunk):
										darken_tile(_RENDER_X, _RENDER_Y, abs(90))
												
						_drawn = True
					
					elif z < _CAMERA_POS[2] and SETTINGS['draw z-levels below']:
						blit_tile(_RENDER_X,_RENDER_Y,map[x][y][z], 'map')
						darken_tile(_RENDER_X,_RENDER_Y,abs((_CAMERA_POS[2]-z))*10)
						_drawn = True
				
					if SETTINGS['draw z-levels above'] and _drawn:
						break
			
			if not _drawn:
				blit_tile(_RENDER_X, _RENDER_Y, BLANK_TILE, 'map')
