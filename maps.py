from globals import *

def create_map():
	_map = []

	for x in range(MAP_SIZE[0]):
		_y = []
		for y in range(MAP_SIZE[1]):
			_z = []
			for z in range(MAP_SIZE[2]):
				_z.append(None)

			_y.append(_z)
		_map.append(_y)

	return _map