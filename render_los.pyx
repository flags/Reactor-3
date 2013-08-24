from globals import *

import cython
import numpy
import time

VERSION = 1

@cython.locals(x=cython.int, y=cython.int)
def draw_circle(x,y,size):
	cdef float circle = 0
	cdef int width=size
	cdef int height=size
	cdef int center_x=(width/2)
	cdef int center_y=(height/2)
	cdef int i,j
	
	_circle = []#[(x+j,y+i)]

	for i in range(height):
		for j in range(width+1):
			circle = (((i-center_y)*(i-center_y))/((float(height)/2)*(float(height)/2)))+((((j-center_x)*(j-center_x))/((float(width)/2)*(float(width)/2))));
			if circle>0 and circle<1.1:
				_circle.append((x+(j-(width/2)),y+(i-(height/2))))
	
	return _circle

def swap(n1,n2):
	return [n2,n1]

@cython.locals(x1=cython.int, y1=cython.int, x2=cython.int, y2=cython.int)
def draw_line(x1,y1,x2,y2):
	path = []
	#if start == end: return None
	
	start = [x1,y1]
	end = [x2,y2]
	
	steep = abs(end[1]-start[1]) > abs(end[0]-start[0])
	
	if steep:
		start = swap(start[0],start[1])
		end = swap(end[0],end[1])
	
	if start[0] > end[0]:
		start[0],end[0] = swap(start[0],end[0])		
		start[1],end[1] = swap(start[1],end[1])
	
	dx = end[0] - start[0]
	dy = abs(end[1] - start[1])
	error = 0
	
	try:
		derr = dy/float(dx)
	except:
		return None
	
	ystep = 0
	y = start[1]
	
	if start[1] < end[1]: ystep = 1
	else: ystep = -1
	
	for x in range(start[0],end[0]+1):
		if steep:
			path.append((y,x))
		else:
			path.append((x,y))
		
		error += derr
		
		if error >= 0.5:
			y += ystep
			error -= 1.0
	
	if not path[0] == (x1,y1):
		path.reverse()
	
	return path

def render_los(map, position, size, top_left=CAMERA_POS, no_edge=False):
	los_buffer = numpy.zeros((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))
	
	cdef int pos1[2]
	cdef int _dark = 0
	cdef int _x,_y
	cdef int X_CAMERA_POS = top_left[0]
	cdef int Y_CAMERA_POS = top_left[1]
	cdef int Z_CAMERA_POS = top_left[2]
	cdef int X_MAP_SIZE = MAP_SIZE[0]
	cdef int Y_MAP_SIZE = MAP_SIZE[1]
	cdef int X_MAP_WINDOW_SIZE = MAP_WINDOW_SIZE[0]
	cdef int Y_MAP_WINDOW_SIZE = MAP_WINDOW_SIZE[1]
	cdef int POSITION[2]
	POSITION[0] = position[0]
	POSITION[1] = position[1]
	
	los_buffer[POSITION[1]-Y_CAMERA_POS,POSITION[0]-X_CAMERA_POS] = 1
	
	for _pos in draw_circle(POSITION[0], POSITION[1], size):
		_dark = 0
		for pos in draw_line(POSITION[0],POSITION[1],_pos[0],_pos[1]):
			_x = pos[0]-X_CAMERA_POS
			_y = pos[1]-Y_CAMERA_POS
			
			if _x<0 or _x>=X_MAP_WINDOW_SIZE or _y<0 or _y>=Y_MAP_WINDOW_SIZE:
				continue
			
			if pos[0]<0 or pos[0]>=X_MAP_SIZE or pos[0]<0 or pos[1]>=Y_MAP_SIZE:
				continue
			
			if map[pos[0]][pos[1]][Z_CAMERA_POS+1]:				
				if not _dark:
					_dark = 1
					
					if not no_edge:
						los_buffer[_y,_x] = 1
					
					continue
				
			if _dark:
				continue

			los_buffer[_y,_x] = 1
	
	return los_buffer
