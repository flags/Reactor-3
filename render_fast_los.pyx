from globals import *

#import drawing
import render_los
import numbers
import numpy
import time
import math

import cython

#start_point = (45, 45)
#source_map = numpy.zeros((100, 100))

cpdef int clip(int number, int start, int end):
	return max(start, min(number, end))

@cython.locals(direction=cython.int, speed=cython.int)
def velocity(direction,speed):
	cdef int rad = direction*(math.pi/180)
	velocity = numpy.multiply(numpy.array([math.cos(rad),math.sin(rad)]),speed)
	
	return [velocity[0],-velocity[1],0]

@cython.locals(sight=cython.int, intensity=cython.int)
def check_dirs(life, sight, source_map, los, intensity=45, already_checked={}, scan=(0, 360), quad_check=True):
	cdef int deg, _i, _x, _y, __x, __y, _wall, _end_x, _end_y, end_point[2], start_point[3], _top_left[3]
	cdef int X_MAP_WINDOW_SIZE = MAP_WINDOW_SIZE[0]
	cdef int Y_MAP_WINDOW_SIZE = MAP_WINDOW_SIZE[1]
	cdef int X_MAP_SIZE = MAP_SIZE[0]
	cdef int Y_MAP_SIZE = MAP_SIZE[1]
	
	_check_dirs = already_checked
	_checked_quads = [deg/90 for deg in already_checked]
	start_point[0] = life['pos'][0]
	start_point[1] = life['pos'][1]
	start_point[2] = life['pos'][2]
	
	for deg in range(scan[0], scan[1], intensity):
		if quad_check and deg/90 in _checked_quads:
			continue
		
		_end_x,_end_y = velocity(deg, sight)[:2]
		end_point[0] = int(start_point[0]+_end_x)
		end_point[1] = int(start_point[1]+_end_y)
		_line = render_los.draw_line(start_point[0], start_point[1], end_point[0], end_point[1])
		_i = 0
		_wall = 0
		__x = clip(start_point[0]-(X_MAP_WINDOW_SIZE/2),0,X_MAP_SIZE)
		__y = clip(start_point[1]-(Y_MAP_WINDOW_SIZE/2),0,Y_MAP_SIZE)
		_top_left[0] = __x
		_top_left[1] = __y
		_top_left[2] = start_point[2]
		
		for pos in _line:
			_x,_y = pos
			_x -= __x
			_y -= __y
			_i += 1
			
			if _x<0 or _x>=MAP_WINDOW_SIZE[0] or _y<0 or _y>=MAP_WINDOW_SIZE[1]:
				continue
			
			if source_map[pos[0]][pos[1]][start_point[2]+1]:
				_check_dirs[deg] = _line[:_i]
				_wall = 1
				continue
			
			if _wall:
				los[_y, _x] = 0
	
	return _check_dirs

def draw_los(life, sight_length, source_map):
	_stime = time.time()
	cdef int sight = sight_length*2
	cdef int intensity = 45
	cdef int quad
	los = numpy.ones((sight, sight))
	
	_check_dirs = {}
	while 1:
		_check_dirs = check_dirs(life, sight, source_map, los, intensity=intensity, already_checked=_check_dirs)
		quads_to_check = [entry/90 for entry in _check_dirs if _check_dirs[entry]]
		intensity /= 2
		
		if intensity<=6:
			break

	for quad in quads_to_check:
		_scan = scan=(numbers.clip(quad*90, 0, 360), (numbers.clip((quad+1)*90, 0, 360)))
		#print _scan
		check_dirs(life, sight, source_map, los, intensity=2, scan=_scan, quad_check=False)
