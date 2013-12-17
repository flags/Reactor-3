#Recursive Shadowcasting
#Implemented in Python by flags
#Original implementation by bjorn.bergstrom@roguelikedevelopment.org
#Source: http://roguebasin.roguelikedevelopment.org/index.php?title=FOV_using_recursive_shadowcasting

#TODO: Move slope/math functions to numbers.py

from globals import *

import alife
import items
import maps

import numpy
import time

MULT = [[1,  0,  0, -1, -1,  0,  0,  1],
        [0,  1, -1,  0,  0, -1,  1,  0],
        [0,  1,  1,  0,  0, -1, -1,  0],
        [1,  0,  0,  1, -1,  0,  0, -1]]
BUFFER_MOD = .25

def draw(los_map, size):
	for y in range(size):
		_x = ''
		for x in range(size):
			if los_map[x, y]:
				_x+=str(int(los_map[x, y]))
			else:
				_x+=' '
			
		print _x

def light(los_map, world_pos, size, row, start_slope, end_slope, xx, xy, yx, yy, callback=None):
	if start_slope < end_slope:
		return False
	
	x, y, z = world_pos
	
	_next_start_slope = start_slope
	
	for i in range(row, size):
		_blocked = False
		
		_d_x = -i
		_d_y = -i
		while _d_x <= 0:
			_l_slope = (_d_x - 0.5) / (_d_y + 0.5)
			_r_slope = (_d_x + 0.5) / (_d_y - 0.5)
			
			if start_slope < _r_slope:
				_d_x += 1
				continue
			elif end_slope>_l_slope:
				break
			
			_sax = _d_x * xx + _d_y * xy
			_say = _d_x * yx + _d_y * yy
			
			if (_sax<0 and abs(_sax)>x) or (_say<0 and abs(_say)>y):
				_d_x += 1
				continue
			
			_a_x = x + _sax
			_a_y = y + _say
			
			if _a_x >= MAP_SIZE[0] or _a_y >= MAP_SIZE[1]:
				_d_x += 1
				continue
			
			_rad2 = size*size
			_solid = maps.is_solid((_a_x, _a_y, z+1))
			
			if (_d_x * _d_x + _d_y * _d_y) < _rad2:
				los_map[_sax+size, _say+size] = 1
				
				if callback and not _solid:
					callback((_a_x, _a_y))
			
			if not _solid:
				_chunk = maps.get_chunk(alife.chunks.get_chunk_key_at((_a_x, _a_y)))
				
				for item_uid in _chunk['items'][:]:
					if not item_uid in ITEMS:
						_chunk['items'].remove(item_uid)
				
				for item_uid in _chunk['items']:
					if items.is_blocking(item_uid):
						_solid = True
						break
			
			if _blocked:
				if _solid:
					_next_start_slope = _r_slope
					_d_x += 1
					continue
				else:
					_blocked = False
					start_slope = _next_start_slope
			elif _solid:
				_blocked = True
				_next_start_slope = _r_slope
				light(los_map, world_pos, size, i+1, start_slope, _l_slope, xx, xy, yx, yy)
			
			_d_x += 1
		
		if _blocked:
			break

def fov(start_position, distance, callback=None):
	_distance = int(round(distance))
	_los = numpy.zeros((_distance*2, _distance*2))
	_start = (start_position[0]-_distance, start_position[1]-_distance, start_position[2])

	for i in range(8):
		light(_los, start_position, _distance, 1, 1.0, 0.0, MULT[0][i],
		      MULT[1][i], MULT[2][i], MULT[3][i], callback=callback);
	
	_los[_los.shape[0]/2,_los.shape[1]/2] = 1
	
	#draw(_los, distance*2)
	
	return _los
