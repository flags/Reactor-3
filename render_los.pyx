from globals import *

import numbers
import cython
import numpy
import alife
import items
import maps
import time

VERSION = 1

@cython.locals(x=cython.int, y=cython.int)
def draw_circle(x,y,size):
	if not size>2:
		size = 2
	
	cdef float circle = 0
	cdef int width=size
	cdef int height=size
	cdef float center_x=(width/2.0)
	cdef float center_y=(height/2.0)
	cdef int i,j
	
	_circle = []

	for i in range(height+1):
		for j in range(width+1):
			circle = (((i-center_y)*(i-center_y))/((float(height)/2)*(float(height)/2)))+((((j-center_x)*(j-center_x))/((float(width)/2)*(float(width)/2))));
			if circle>0 and circle<1.1:
				_circle.append((x+(j-(width//2)),y+(i-(height//2))))
	
	if not (x, y) in _circle:
		_circle.append((x, y))
	
	return _circle

def swap(n1,n2):
	return [n2,n1]

@cython.locals(x1=cython.int, y1=cython.int, x2=cython.int, y2=cython.int)
def draw_line(x1,y1,x2,y2):
	path = []
	if (x1, y1) == (x2, y2):
		return [(x2, y2)]
	
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

def render_los(position, size, view_size=MAP_WINDOW_SIZE, top_left=CAMERA_POS, no_edge=False, visible_chunks=None, life=None):
	los_buffer = numpy.zeros((view_size[1], view_size[0]))
	
	cdef int _dark = 0
	cdef int _x,_y
	cdef int X_CAMERA_POS = top_left[0]
	cdef int Y_CAMERA_POS = top_left[1]
	cdef int Z_CAMERA_POS = top_left[2]
	cdef int X_MAP_SIZE = MAP_SIZE[0]
	cdef int Y_MAP_SIZE = MAP_SIZE[1]
	cdef int X_MAP_WINDOW_SIZE = view_size[0]
	cdef int Y_MAP_WINDOW_SIZE = view_size[1]
	cdef int POS_X, POS_Y
	POS_X = position[0]
	POS_Y = position[1]
	
	#SKIP_CHUNKS = []
	VISIBLE_CHUNKS = []
	if life and alife.brain.get_flag(life, 'visible_chunks'):
		VISIBLE_CHUNKS = alife.brain.get_flag(life, 'visible_chunks')
		
		#for chunk_key in alife.brain.get_flag(life, 'visible_chunks'):
		#	if maps.get_chunk(chunk_key)['max_z'] > life['pos'][2]:
		#		SKIP_CHUNKS.append(chunk_key)
	
	#if not POS_X-X_CAMERA_POS<0 and not POS_X-X_CAMERA_POS >= X_MAP_WINDOW_SIZE and not POS_Y-Y_CAMERA_POS<0 and not POS_Y-Y_CAMERA_POS >= Y_MAP_WINDOW_SIZE:
	#	los_buffer[POS_Y-Y_CAMERA_POS,POS_X-X_CAMERA_POS] = 1
	
	for _pos in draw_circle(POS_X, POS_Y, size):
		_dark = 0
		
		_chunk_key = '%s,%s' % ((_pos[0]//WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'],
			(_pos[1]//WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'])
			
		#if _chunk_key in HIDDEN_CHUNKS:
		#	continue
		
		for pos in draw_line(POS_X,POS_Y,_pos[0],_pos[1]):
			_x = pos[0]-X_CAMERA_POS
			_y = pos[1]-Y_CAMERA_POS
			#_distance = 1#numbers.clip(numbers.distance(pos, (POS_X, POS_Y), old=True), 1, 255)*.10
			
			if _x<0 or _x>=X_MAP_WINDOW_SIZE or _y<0 or _y>=Y_MAP_WINDOW_SIZE:
				continue
			
			if pos[0]<0 or pos[0]>=X_MAP_SIZE or pos[0]<0 or pos[1]>=Y_MAP_SIZE:
				continue
			
			if maps.is_solid((pos[0], pos[1], Z_CAMERA_POS+1)):
				if not _dark:
					if not no_edge:
						los_buffer[_y,_x] = 1
					
					break
			else:
				_chunk = alife.chunks.get_chunk(alife.chunks.get_chunk_key_at((pos[0], pos[1], Z_CAMERA_POS)))
				_break = False
				
				for item_uid in _chunk['items'][:]:
					if not item_uid in ITEMS:
						_chunk['items'].remove(item_uid)
				
				for item in [ITEMS[uid] for uid in _chunk['items'] if items.is_blocking(uid)]:
					if tuple(item['pos']) == (pos[0], pos[1], Z_CAMERA_POS):
						if not _dark:
							if not no_edge:
								los_buffer[_y,_x] = 1
						
							_break = True
							break
				
				if _break:
					break

			los_buffer[_y,_x] = 1
	
	return los_buffer
