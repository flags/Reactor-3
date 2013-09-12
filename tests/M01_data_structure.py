GRASS_TILE = {'id':'grass',
	'icon':'.',
	'color':'green',
	'burnable':True,
	'cost':1}

DIRT_TILE = {'id':'dirt',
	'icon':'.',
	'color':'brown',
	'burnable':False,
	'cost':2}

TILES = [GRASS_TILE,DIRT_TILE]
MAP = []

def create_tile(tile):
	_ret_tile = {}
	_ret_tile['id'] = tile['id']
	
	_ret_tile['items'] = []
	_ret_tile['fire'] = 0
	
	return _ret_tile

def get_raw_tile(tile):
	for _tile in TILES:
		if _tile['id'] == tile['id']:
			return _tile
	
	raise Exception

for x in range(400):
	_y = []
	for y in range(400):
		_y.append(create_tile(DIRT_TILE))
	
	MAP.append(_y)

print MAP[3][3],get_raw_tile(MAP[3][3])['cost']

import sys
print 'Map size (bytes):',sys.getsizeof(MAP)