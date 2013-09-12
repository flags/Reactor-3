from globals import *
from tiles import *

import zones
import maps

import random
import copy
import sys

def get_map_size(map):
	return (len(map),len(map[0]),len(map[0][0]))

def resize_map(map,size):
	_old_size = get_map_size(map)
	
	if _old_size[0]>size[0] or _old_size[1]>size[1] or _old_size[2]>size[2]:
		print 'Warning: Attempting to shink the map! Data will be lost.'
	
	_new_map = copy.deepcopy(map)
	
	if _old_size[0]>size[0]:
		for x in range(abs(_old_size[0]-size[0])):
			_new_map.pop()
	elif _old_size[0]<size[0]:
		for x1 in range(abs(_old_size[0]-size[0])):
			_y1 = []
			for y1 in range(_old_size[1]):
				_z1 = []
				for z1 in range(_old_size[2]):
					if z1 == 2:
						_z1.append(create_tile(random.choice(
							[TALL_GRASS_TILE,SHORT_GRASS_TILE,GRASS_TILE])))
					else:
						_z1.append(None)
				
				_y1.append(_z1)
			
			_new_map.append(_y1)

	_old_size = get_map_size(_new_map)
	
	if _old_size[1]>size[1]:
		for x in range(size[0]):
			for y in range(abs(_old_size[1]-size[1])):
				_new_map[x].pop()
	elif _old_size[1]<size[1]:
		for x1 in range(_old_size[0]):
			_y1 = []
			for y1 in range(abs(_old_size[1]-size[1])):
				_z1 = []
				for z1 in range(_old_size[2]):
					if z1 == 2:
						_z1.append(create_tile(random.choice(
							[TALL_GRASS_TILE,SHORT_GRASS_TILE,GRASS_TILE])))
					else:
						_z1.append(None)
				
				_new_map[x1].append(_z1)
	
	_old_size = get_map_size(_new_map)
	
	if _old_size[2]>size[2]:
		for x1 in range(_old_size[0]):
			for y1 in range(_old_size[1]):
				for z in range(abs(_old_size[2]-size[2])):
					_new_map[x1][y1].pop()
	elif _old_size[2]<size[2]:
		for x1 in range(_old_size[0]):
			_y1 = []
			for y1 in range(abs(_old_size[1])):
				_z1 = []
				for z1 in range(abs(_old_size[2]-size[2])):
					_z1.append(None)
			
				_new_map[x1][y1].extend(_z1)
	
	return _new_map

if __name__ == '__main__':
	if '--create' in sys.argv:
		create_all_tiles()
		WORLD_INFO['map'] = maps.create_map()
		maps.create_position_maps()
		maps.update_chunk_map()
		
		zones.create_zone_map()
		zones.connect_ramps()
		
		maps.save_map('temp_map.dat')
		
		print 'Created map: temp_map.dat'