#Recursive Shadowcasting
#Implemented in Python by flags
#Original implementation by bjorn.bergstrom@roguelikedevelopment.org
#Source: http://roguebasin.roguelikedevelopment.org/index.php?title=FOV_using_recursive_shadowcasting

#TODO: Move slope/math functions to numbers.py

import numpy
import time


BUFFER_MOD = .15
WORLD_INFO = {}
WORLD_INFO['map'] = []

for x in range(40):
	_y = []
	for y in range(40):
		_y.append(0)
	
	WORLD_INFO['map'].append(_y)

WORLD_INFO['map'][15][10] = 1

def draw(los_map):
	for y in range(40):
		for x in range(40):
			if (x, y) == (20, 20):
				print 'X',
			elif WORLD_INFO['map'][x][y]:
				print '#',
			else:
				if los_map[x, y]:
					print '.',
				else:
					print 'o',
		
		print

def slope(start_pos, end_pos):
	return (start_pos[0] - end_pos[0]) / float(start_pos[1] - end_pos[1])

def inverse_slope(start_pos, end_pos):
	return 1 / slope(start_pos, end_pos)

def walk_northeast(los_map, start_pos, l_slope=1, r_slope=0, pos_mod=[0, 0], row=1):
	#if not l_slope == 1:
	#	print l_slope
	_x = -row
	_max_x = 0
	_y = -row
	_blocked = False
	_n_l_slope = l_slope
	
	for i in range(0, row):
		_x += 1
		_slope = slope((0, 0), (_x, _y))
		#WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]] = 2
		
		#print r_slope, _slope, l_slope
		if _slope <= r_slope or _slope >= l_slope:
			continue
		
		if WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]]:
			_slope = slope((0, 0), (_x+BUFFER_MOD, _y))
			#print r_slope, l_slope, (0, 0), (_x, _y), _slope
			walk_northeast(los_map, start_pos, row=row+1, r_slope=_slope, l_slope=l_slope)
			_blocked = True
			continue
		elif _blocked:
			print _slope
			_n_l_slope = _slope
			_blocked = False
		
		if start_pos[0]+_x<0 or start_pos[1]+_y<0:
			break
		
		#print _x+start_pos[0], _y+start_pos[1]
		los_map[_x+start_pos[0]][_y+start_pos[1]] = 1
		
	draw(los_map)
	#print 'fin'
	
	#print start_pos[0]+_x, start_pos[1]+_y, _x, _y
	if start_pos[0]+_x<0 or start_pos[1]+_y<0:
		return False
	
	#if not _blocked:
	#print _n_l_slope, r_slope
	if not WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]]:
		walk_northeast(los_map, start_pos, row=row+1, l_slope=_n_l_slope, r_slope=r_slope)
	
	#start_pos[0]

def los(start_position, distance):
	_los = numpy.zeros((distance, distance))
	
	#TODO: Repeat for other octants
	walk_northeast(_los, (20, 20))

_start_time = time.time()
los((20, 20), 40)
print time.time()-_start_time

