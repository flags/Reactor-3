SHORT_GRASS_TILE = {'id':'short_grass',
	'icon':'.',
	'color':'green',
	'burnable':True,
	'cost':1}

GRASS_TILE = {'id':'grass',
	'icon':',',
	'color':'green',
	'burnable':True,
	'cost':1}

TALL_GRASS_TILE = {'id':'tall_grass',
	'icon':';',
	'color':'green',
	'burnable':True,
	'cost':1}

DIRT_TILE = {'id':'dirt',
	'icon':'.',
	'color':'brown',
	'burnable':False,
	'cost':2}

TILES = [SHORT_GRASS_TILE,GRASS_TILE,TALL_GRASS_TILE,DIRT_TILE]
MAP = []
MAP_SIZE = (50,50,5)

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
	
import random

for x in range(MAP_SIZE[0]):
	_y = []
	for y in range(MAP_SIZE[1]):
		_z = []
		for z in range(MAP_SIZE[2]):
			if z == 0:
				_z.append(create_tile(DIRT_TILE))
			elif z == 1:
				_z.append(create_tile(random.choice([GRASS_TILE,SHORT_GRASS_TILE,TALL_GRASS_TILE])))
			else:
				_z.append(None)
		
		_y.append(_z)
	MAP.append(_y)

print('Printing map')
for x in range(MAP_SIZE[0]):
	for y in range(MAP_SIZE[1]):
		_top_tile = None
		for z in range(MAP_SIZE[2]):
			if MAP[x][y][z]:
				_top_tile = MAP[x][y][z]
		
		print(get_raw_tile(_top_tile)['icon'], end=' ')
	
	print()

print('Timing map fetching')
import time
_stime = time.time()
for x in range(MAP_SIZE[0]):
	for y in range(MAP_SIZE[1]):
		for z in range(MAP_SIZE[2]):
			if MAP[x][y][z]:
				get_raw_tile(MAP[x][y][z])
print(time.time()-_stime)

print(MAP[3][3])