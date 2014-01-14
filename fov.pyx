#Recursive Shadowcasting
#Implemented in Python by flags
#Original implementation by bjorn.bergstrom@roguelikedevelopment.org
#Source: http://roguebasin.roguelikedevelopment.org/index.php?title=FOV_using_recursive_shadowcasting

from globals import *

import numbers
import alife
import items
import maps

import cPickle
import cython
import numpy
import time

MULT = [[1,  0,  0, -1, -1,  0,  0,  1],
	[0,  1, -1,  0,  0, -1,  1,  0],
	[0,  1,  1,  0,  0, -1, -1,  0],
	[1,  0,  0,  1, -1,  0,  0, -1]]


@cython.locals(size=cython.int, row=cython.int, _start_slope=cython.float, _end_slope=cython.float, xx=cython.int, xy=cython.int, yx=cython.int, yy=cython.int)
def light(los_map, world_pos, size, row, _start_slope, _end_slope, xx, xy, yx, yy, source_map, map_size, chunk_map, callback=None):
	_return_chunks = set()
	
	if _start_slope < _end_slope:
		return los_map, _return_chunks
	
	cdef int i, x, y, z, _d_x, _d_y, _sax, _say, _a_x, _a_y
	cdef float _l_slope, _r_slope, start_slope, end_slope
	
	start_slope = _start_slope
	end_slope = _end_slope
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
			
			if _a_x >= map_size[0] or _a_y >= map_size[1]:
				_d_x += 1
				continue
			
			_rad2 = size*size
			_solid = maps.is_solid((_a_x, _a_y, z+1), source_map=source_map)
			
			if (_d_x * _d_x + _d_y * _d_y) < _rad2:
				los_map[_sax+size, _say+size] = 1
				
				if callback and not _solid:
					callback((_a_x, _a_y))
			
			if not _solid:
				_chunk_key = '%s,%s' % ((_a_x/5)*5, (_a_y/5)*5)
				_chunk = chunk_map[_chunk_key]
				
				for item_uid in _chunk['items'][:]:
					if not item_uid in ITEMS:
						_chunk['items'].remove(item_uid)
				
				for item_uid in _chunk['items']:
					if items.is_blocking(item_uid) and ITEMS[item_uid]['pos'][:2] == [_a_x, _a_y]:
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
				_map, _chunk_keys = light(los_map, world_pos, size, i+1, start_slope, _l_slope, xx, xy, yx, yy, source_map, map_size, chunk_map, callback=callback)
			
			_d_x += 1
		
		if _blocked:
			break
	
	return los_map, _return_chunks

def fov(start_position, distance, get_chunks=False, life_id=None, callback=None):
	_distance = int(round(distance))
	_los = numpy.zeros((_distance*2, _distance*2))
	_start = (start_position[0]-_distance, start_position[1]-_distance, start_position[2])
	_chunk_keys = []
	_rays = {}
	
	_collision_map = numpy.zeros((_distance*2, _distance*2))
	
	if get_chunks:
		_chunks_with_items = {}
		
		for y in range(start_position[1]-_distance, start_position[1]+_distance, WORLD_INFO['chunk_size']):
			for x in range(start_position[0]-_distance, start_position[0]+_distance, WORLD_INFO['chunk_size']):
				if x<0 or x>=MAP_SIZE[0]-1 or y<0 or y>=MAP_SIZE[1]-1:
					continue
				
				_chunk_key = '%s,%s' % ((x/5)*5, (y/5)*5)
				
				for item_uid in maps.get_chunk(_chunk_key)['items']:
					if items.is_blocking(item_uid) and ITEMS[item_uid]['pos'][:2] == [x, y]:
						if _chunk_key in _chunks_with_items:
							_chunks_with_items[_chunk_key].append(item_uid)
						else:
							_chunks_with_items[_chunk_key] = [item_uid]
		
		for y in range(start_position[1]-_distance, start_position[1]+_distance):
			for x in range(start_position[0]-_distance, start_position[0]+_distance):
				if x<0 or x>=MAP_SIZE[0]-1 or y<0 or y>=MAP_SIZE[1]-1:
					continue
				
				if not maps.is_solid((x, y, start_position[2]+1)):
					_collision_map[x-start_position[0], y-start_position[1]] = 1
					
					continue
				
				_chunk_key = alife.chunks.get_chunk_key_at((x, y))
				
				if _chunk_key in _chunks_with_items:
					for item_uid in _chunks_with_items[_chunk_key][:]:
						if ITEMS[item_uid]['pos'][:2] == [x, y]:
							_collision_map[x-start_position[0], y-start_position[1]] = 1
							_chunks_with_items[_chunk_key].remove(item_uid)
							
							break
					
					if not _chunks_with_items[_chunk_key]:
						del _chunks_with_items[_chunk_key]
	
		#cPickle.dumps(_collision_map)
		#_t = time.time()
		#cPickle.dumps(_active_items)
		#print 'took', time.time()-_t

	for i in range(8):
		if get_chunks:
			FOV_JOBS[life_id] = SETTINGS['smp'].submit(pyfov.old_light,
				(_los, start_position, _distance, 1, 1.0, 0.0, MULT[0][i],
					MULT[1][i], MULT[2][i], MULT[3][i], _collision_map, MAP_SIZE,),
				(), ('pyfov',))
			
		else:
			_map, _keys = light(_los, start_position, _distance, 1, 1.0, 0.0, MULT[0][i],
				MULT[1][i], MULT[2][i], MULT[3][i], WORLD_INFO['map'], MAP_SIZE, WORLD_INFO['chunk_map'], callback=callback)

	_los[_los.shape[0]/2,_los.shape[1]/2] = 1

	if get_chunks:
		return False

	return _los
