from globals import *

import render_los
import numbers
import numpy
import time
import math

import cython

cpdef int clip(int number, int start, int end):
	return max(start, min(number, end))

@cython.locals(direction=cython.int, speed=cython.int)
def velocity(direction,speed):
	cdef double rad = direction*(math.pi/180)
	velocity = numpy.multiply(numpy.array([math.cos(rad),math.sin(rad)]),speed)
	
	return [velocity[0],-velocity[1],0]

@cython.locals(sight=cython.int, intensity=cython.int)
def check_dirs(at, sight, source_map, los, intensity=45, already_checked={}, scan=(0, 360), quad_check=True, no_edge=False):
	cdef int deg, _i, _x, _y, __x, __y, _wall, _end_x, _end_y, end_point[2], start_point[3], _top_left[3]
	cdef int X_MAP_WINDOW_SIZE = MAP_WINDOW_SIZE[0]
	cdef int Y_MAP_WINDOW_SIZE = MAP_WINDOW_SIZE[1]
	cdef int X_MAP_SIZE = MAP_SIZE[0]
	cdef int Y_MAP_SIZE = MAP_SIZE[1]
	
	_check_dirs = already_checked
	_checked_quads = [deg//90 for deg in already_checked]
	start_point[0] = at[0]
	start_point[1] = at[1]
	start_point[2] = at[2]
	
	for deg in range(scan[0], scan[1], intensity):
		if quad_check and deg//90 in _checked_quads:
			continue
		
		_end_x,_end_y = velocity(deg, sight)[:2]
		end_point[0] = start_point[0]+int(round(_end_x))
		end_point[1] = start_point[1]+int(round(_end_y))
		_line = render_los.draw_line(start_point[0], start_point[1], end_point[0], end_point[1])
		_i = 0
		_wall = 0
		__x = clip(start_point[0]-(los.shape[1]//2),0,X_MAP_SIZE-(los.shape[1]//2))
		__y = clip(start_point[1]-(los.shape[0]//2),0,Y_MAP_SIZE-(los.shape[0]//2))
		
		for pos in _line:
			_x,_y = pos
			_x -= __x
			_y -= __y
			_i += 1
			
			if _x<0 or _x>=los.shape[1]-1 or _y<0 or _y>=los.shape[0]-1 or pos[0]>=MAP_SIZE[0]-1 or pos[1]>=MAP_SIZE[1]-1:
				continue
			
			if source_map[pos[0]][pos[1]][start_point[2]+1]:
				_check_dirs[deg] = _line[:_i]
				if not _wall:
					_wall = 1
				
					if not no_edge:
						los[_y, _x] = 0
				
					continue
			
			if _wall:
				los[_y, _x] = 0
	
	return _check_dirs

def render_fast_los(at, sight_length, source_map, no_edge=False):
	_stime = time.time()
	cdef int sight = sight_length
	cdef int intensity = 45
	cdef int quad
	los = numpy.ones((sight, sight))
	
	_check_dirs = {}
	while 1:
		_check_dirs = check_dirs(at, sight, source_map, los, intensity=intensity, already_checked=_check_dirs, no_edge=no_edge)
		quads_to_check = []
		
		for deg in [entry//90 for entry in _check_dirs if _check_dirs[entry]]:
			if not deg in quads_to_check:
				quads_to_check.append(deg)
		
		intensity //= 2
		
		if intensity<=6:
			break

	_cover = {'pos': None,'score':9000}
	for quad in quads_to_check:
		_scan = scan=(numbers.clip(quad*90, 0, 360), (numbers.clip((quad+1)*90, 0, 360)))
		_check_dirs = check_dirs(at, sight, source_map, los, intensity=1, scan=_scan, quad_check=False, no_edge=no_edge)
	
	return los
