#Recursive Shadowcasting
#Implemented in Python by flags
#Original implementation by bjorn.bergstrom@roguelikedevelopment.org
#Source: http://roguebasin.roguelikedevelopment.org/index.php?title=FOV_using_recursive_shadowcasting

#TODO: Move slope/math functions to numbers.py

import numpy
import time

MULT = [[1,  0,  0, -1, -1,  0,  0,  1],
        [0,  1, -1,  0,  0, -1,  1,  0],
        [0,  1,  1,  0,  0, -1, -1,  0],
        [1,  0,  0,  1, -1,  0,  0, -1]]

MAP_SIZE = [40, 40]
BUFFER_MOD = .25
WORLD_INFO = {}
WORLD_INFO['map'] = []

for x in range(40):
	_y = []
	for y in range(40):
		_y.append(0)

	WORLD_INFO['map'].append(_y)

for i in range(0, 40):
	if i%3:
		WORLD_INFO['map'][10][i] = 1
	#if i%2:
	#        WORLD_INFO['map'][7][i] = 1
	#WORLD_INFO['map'][i][5] = 1

#WORLD_INFO['map'][21][20] = 1

def draw(los_map):
	for y in range(40):
		_x = ''
		for x in range(40):
			if (x, y) == (20, 20):
				_x+='X'
			elif WORLD_INFO['map'][x][y]:
				_x+='#'
			else:
				if los_map[x, y]:
					_x+=str(int(los_map[x, y]))
				else:
					_x+=' '

		print _x

def slope(start_pos, end_pos):
	return (start_pos[0] - end_pos[0]) / float(start_pos[1] - end_pos[1])

def inverse_slope(start_pos, end_pos):
	return 1 / slope(start_pos, end_pos)

def light(los_map, world_pos, size, row, start_slope, end_slope, xx, xy, yx, yy):
	if start_slope < end_slope:
		return False
	
	x, y = world_pos
	
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
			
			if (_d_x * _d_x + _d_y * _d_y) < _rad2:
				los_map[_a_x, _a_y] = 1
			
			_solid = WORLD_INFO['map'][_a_x][_a_y]
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


def los(start_position, distance):
	_los = numpy.zeros((distance*2, distance*2))

	for i in range(8):
		light(_los, start_position, distance, 1, 1.0, 0.0, MULT[0][i],
		      MULT[1][i], MULT[2][i], MULT[3][i]);
	#walk_row(_los, (20, 20), octant=(-1, -1))
	#walk_row(_los, (20, 20), octant=(1, -1))
	#walk_row(_los, (20, 20), octant=(-1, 1))
	#walk_row(_los, (20, 20), octant=(1, 1))

	#walk_col(_los, (20, 20), octant=(-1, -1))
	#walk_col(_los, (20, 20), octant=(-1, 1))
	#walk_col(_los, (20, 20), octant=(1, -1))
	#walk_col(_los, (20, 20), octant=(1, 1))

	return _los

_start_time = time.time()
_los = los((20, 20), 20)
print time.time()-_start_time

draw(_los)