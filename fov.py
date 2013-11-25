#Recursive Shadowcasting
#Implemented in Python by flags
#Original implementation by bjorn.bergstrom@roguelikedevelopment.org
#Source: http://roguebasin.roguelikedevelopment.org/index.php?title=FOV_using_recursive_shadowcasting

#TODO: Move slope/math functions to numbers.py

import numpy
import time


BUFFER_MOD = .25
WORLD_INFO = {}
WORLD_INFO['map'] = []

for x in range(40):
	_y = []
	for y in range(40):
		_y.append(0)
	
	WORLD_INFO['map'].append(_y)

WORLD_INFO['map'][11][3] = 1
WORLD_INFO['map'][11][17] = 1
WORLD_INFO['map'][11][22] = 1
WORLD_INFO['map'][18][10] = 1
WORLD_INFO['map'][25][7] = 1
WORLD_INFO['map'][28][7] = 1
WORLD_INFO['map'][28][18] = 1
WORLD_INFO['map'][28][22] = 1
WORLD_INFO['map'][11][35] = 1
WORLD_INFO['map'][25][35] = 1

def draw(los_map):
	for y in range(40):
		for x in range(40):
			if (x, y) == (20, 20):
				print 'X',
			elif WORLD_INFO['map'][x][y]:
				print '#',
			else:
				if los_map[x, y]:
					print int(los_map[x, y]),
				else:
					print ' ',
		
		print

def slope(start_pos, end_pos):
	return (start_pos[0] - end_pos[0]) / float(start_pos[1] - end_pos[1])

def inverse_slope(start_pos, end_pos):
	return 1 / slope(start_pos, end_pos)

def walk_row(los_map, start_pos, l_slope=1, r_slope=0, octant=(0, 0), row=1, _id=1):
	_x = row*octant[0]
	_y = row*octant[1]
	_blocked = False
	_n_l_slope = l_slope
	
	for i in range(0, row):
		_x += -1*octant[0]
		_slope = abs(slope((0, 0), (_x, _y)))

		if _slope <= r_slope or _slope >= l_slope:
			continue
		
		if WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]]:
			_slope = abs(slope((0, 0), (_x+(BUFFER_MOD*octant[0]), _y)))
			_blocked = True
			walk_row(los_map, start_pos, row=row+1, r_slope=_slope, l_slope=_n_l_slope, _id=_id+1, octant=octant)
			
			continue
		elif _blocked:
			_n_l_slope = _slope
			_blocked = False
		
		if start_pos[0]+_x<=0 or start_pos[1]+_y<=0 or start_pos[0]+_x>=los_map.shape[0] or start_pos[1]+_y>=los_map.shape[1]:
			break
		
		los_map[_x+start_pos[0]][_y+start_pos[1]] = _id
	
	if start_pos[0]+_x<0 or start_pos[1]+_y<0 or start_pos[0]+_x>=los_map.shape[0]-1 or start_pos[1]+_y>=los_map.shape[1]-1:
		return los_map
	
	if not WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]]:
		walk_row(los_map, start_pos, row=row+1, l_slope=_n_l_slope, r_slope=r_slope, _id=_id, octant=octant)

	return los_map

def walk_col(los_map, start_pos, l_slope=1, r_slope=0, octant=(0, 0), row=1, _id=1):
	_x = row*octant[0]
	_y = row*octant[1]
	_blocked = False
	_n_l_slope = l_slope
	
	for i in range(0, row):
		_y += -1*octant[1]
		_slope = abs(slope((0, 0), (_y, _x)))
		
		if _slope <= r_slope or _slope >= l_slope:
			continue
		
		if WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]]:
			_slope = abs(slope((0, 0), (_y+(BUFFER_MOD*octant[0]), _x)))
			_blocked = True
			walk_col(los_map, start_pos, row=row+1, r_slope=_slope, l_slope=_n_l_slope, _id=_id+1, octant=octant)
			
			continue
		elif _blocked:
			_n_l_slope = _slope
			_blocked = False
		
		if start_pos[0]+_x<=0 or start_pos[1]+_y<=0 or start_pos[0]+_x>=los_map.shape[0] or start_pos[1]+_y>=los_map.shape[1]:
			break
		
		los_map[_x+start_pos[0]][_y+start_pos[1]] = _id
	
	if start_pos[0]+_x<0 or start_pos[1]+_y<0 or start_pos[0]+_x>=los_map.shape[0]-1 or start_pos[1]+_y>=los_map.shape[1]-1:
		return los_map
	
	if not WORLD_INFO['map'][_x+start_pos[0]][_y+start_pos[1]]:
		walk_col(los_map, start_pos, row=row+1, l_slope=_n_l_slope, r_slope=r_slope, _id=_id, octant=octant)

	return los_map

def los(start_position, distance):
	_los = numpy.zeros((distance, distance))
	
	#TODO: Repeat for other octants
	walk_row(_los, (20, 20), octant=(-1, -1))
	walk_row(_los, (20, 20), octant=(1, -1))
	walk_row(_los, (20, 20), octant=(-1, 1))
	walk_row(_los, (20, 20), octant=(1, 1))
	
	walk_col(_los, (20, 20), octant=(-1, -1))
	walk_col(_los, (20, 20), octant=(-1, 1))
	walk_col(_los, (20, 20), octant=(1, -1))
	walk_col(_los, (20, 20), octant=(1, 1))
	#walk_northeast(_los, (20, 20))
	
	#print draw(_los)
	
	return _los

_start_time = time.time()
_los = los((20, 20), 40)
print time.time()-_start_time
