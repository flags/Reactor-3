#Recursive Shadowcasting
#Implemented in Python by flags
#Original implementation by bjorn.bergstrom@roguelikedevelopment.org
#Source: http://roguebasin.roguelikedevelopment.org/index.php?title=FOV_using_recursive_shadowcasting

#TODO: Move slope/math functions to numbers.py

from globals import *

import maps

import numpy
import time


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

def slope(start_pos, end_pos):
	return (start_pos[0] - end_pos[0]) / float(start_pos[1] - end_pos[1])

def inverse_slope(start_pos, end_pos):
	return 1 / slope(start_pos, end_pos)

def walk_row(los_map, start_pos, los_size, l_slope=1, r_slope=0, octant=(0, 0), row=1, _id=1):
	_x = (row*octant[0])+octant[0]
	_y = row*octant[1]
	_blocked = False
	_n_l_slope = l_slope
	
	for i in range(0, row+1):
		_x += -1*octant[0]		
		_w_x = (los_size/2)+_x
		_w_y = (los_size/2)+_y
		_d_x = start_pos[0]+_x
		_d_y = start_pos[1]+_y
		_slope = abs(slope((0, 0), (_x, _y)))

		if _slope < r_slope or _slope > l_slope:
			continue
		
		if _w_x<0 or _w_y<=0 or _w_x>=los_map.shape[0]-1 or _w_y>=los_map.shape[1]-1 or _d_x>=MAP_SIZE[0]-1 or _d_y>=MAP_SIZE[1]-1:
			continue
		
		if maps.is_solid((_d_x, _d_y, start_pos[2]+1)):
			_slope = abs(slope((0, 0), (_x+(BUFFER_MOD*octant[0]), _y)))
			_blocked = True
			walk_row(los_map, start_pos, los_size, row=row+1, r_slope=_slope, l_slope=_n_l_slope, _id=_id+1, octant=octant)
			
			if _w_x<0 or _w_y<=0 or _w_x>=los_map.shape[0]-1 or _w_y>=los_map.shape[1]-1 or _d_x>=MAP_SIZE[0]-1 or _d_y>=MAP_SIZE[1]-1:
				pass
			else:
				print 'breaking'
				continue
		elif _blocked:
			_n_l_slope = _slope
			_blocked = False
		
		print 'here'
		los_map[_w_x][_w_y] = _id
	
	if _w_x<0 or _w_y<=0 or _w_x>=los_map.shape[0]-1 or _w_y>=los_map.shape[1]-1 or _d_x>=MAP_SIZE[0]-1 or _d_y>=MAP_SIZE[1]-1:
		print 'broke'
		return los_map
	
	if not maps.is_solid((_d_x, _d_y, start_pos[2]+1)):
		walk_row(los_map, start_pos, los_size, row=row+1, l_slope=_n_l_slope, r_slope=r_slope, _id=_id, octant=octant)

	return los_map

def walk_col(los_map, start_pos, los_size, l_slope=1, r_slope=0, octant=(0, 0), row=1, _id=1):
	_x = row*octant[0]
	_y = row*octant[1]
	_blocked = False
	_n_l_slope = l_slope
	
	for i in range(0, row):
		_w_x = (los_size/2)+_x
		_w_y = (los_size/2)+_y
		_d_x = start_pos[0]+_w_x
		_d_y = start_pos[1]+_w_y
		_y += -1*octant[1]
		_slope = 1/abs(slope((0, -.1*octant[1]), (_x, _y)))
		
		if _slope < r_slope or _slope > l_slope:
			continue
		
		if _w_x<0 or _w_y<=0 or _w_x>=los_map.shape[0]-1 or _w_y>=los_map.shape[1]-1 or _d_x>=MAP_SIZE[0]-1 or _d_y>=MAP_SIZE[1]-1:
			continue
		
		if maps.is_solid((_w_x, _w_y, start_pos[2])):
			_slope = abs(slope((0, 0), (_y+(BUFFER_MOD*octant[0]), _x)))
			_blocked = True
			walk_col(los_map, start_pos, los_size, row=row+1, r_slope=_slope, l_slope=_n_l_slope, _id=_id+1, octant=octant)
			
			if _w_x<0 or _w_y<=0 or _w_x>=los_map.shape[0]-1 or _w_y>=los_map.shape[1]-1 or _d_x>=MAP_SIZE[0]-1 or _d_y>=MAP_SIZE[1]-1:
				pass
			else:
				continue
		elif _blocked:
			_n_l_slope = _slope
			_blocked = False
		
		print 'here'
		los_map[_x+start_pos[0]][_y+start_pos[1]] = _id
	
	if _w_x<0 or _w_y<=0 or _w_x>=los_map.shape[0]-1 or _w_y>=los_map.shape[1]-1 or _d_x>=MAP_SIZE[0]-1 or _d_y>=MAP_SIZE[1]-1:
		return los_map
	
	if not WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]]:
		walk_col(los_map, start_pos, los_size, row=row+1, l_slope=_n_l_slope, r_slope=r_slope, _id=_id, octant=octant)

	return los_map

def fov(start_position, distance):
	_los = numpy.zeros((distance, distance))
	
	walk_row(_los, start_position, distance, octant=(-1, -1))
	walk_row(_los, start_position, distance, octant=(1, -1))
	walk_row(_los, start_position, distance, octant=(-1, 1))
	walk_row(_los, start_position, distance, octant=(1, 1))
	
	#walk_col(_los, start_position, distance, octant=(-1, -1))
	#walk_col(_los, start_position, distance, octant=(-1, 1))
	#walk_col(_los, start_position, distance, octant=(1, -1))
	#walk_col(_los, start_position, distance, octant=(1, 1))
	
	draw(_los, distance)
	
	return _los
