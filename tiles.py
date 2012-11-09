from libtcodpy import *
from globals import *

BLANK_TILE = {'id':'blank_tile',
				'icon': '.',
				'color':(darker_gray,black)}

SHORT_GRASS_TILE = {'id':'short_grass',
                    'icon':'.',
                    'color':(GRASS_GREEN_DARK,GRASS_GREEN),
                    'burnable':True,
                    'cost':1}

GRASS_TILE = {'id':'grass',
              'icon':';',
              'color':(GRASS_GREEN,GRASS_GREEN_DARK),
              'burnable':True,
              'cost':1}

TALL_GRASS_TILE = {'id':'tall_grass',
                   'icon':'\\',
                   'color':(GRASS_GREEN,GREEN_ALT),
                   'burnable':True,
                   'cost':1}

DIRT_TILE = {'id':'dirt',
             'icon':'.',
             'color':(SAND_LIGHT,SAND),
             'burnable':False,
             'cost':2}

SAND_TILE_1 = {'id':'sand_1',
             'icon':'.',
             'color':(SAND_LIGHT,SAND),
             'burnable':False,
             'cost':2}

SAND_TILE_2 = {'id':'sand_2',
             'icon':'\\',
             'color':(SAND,SAND_LIGHT),
             'burnable':False,
             'cost':2}

DIRT_TILE_1 = {'id':'dirt_1',
             'icon':'\\',
             'color':(BROWN_DARK,BROWN_DARK_ALT),
             'burnable':False,
             'cost':2}

DIRT_TILE_2 = {'id':'dirt_2',
             'icon':',',
             'color':(BROWN_DARK_ALT,BROWN_DARK),
             'burnable':False,
             'cost':2}

DIRT_TILE_3 = {'id':'dirt_3',
             'icon':'.',
             'color':(BROWN_DARK_ALT,BROWN_DARK_ALT_2),
             'burnable':False,
             'cost':2}

WALL_TILE = {'id':'wall',
             'icon':'#',
             'color':(black,gray),
             'burnable':False,
             'cost':-1}

#Groups
TILES = [BLANK_TILE,
		DIRT_TILE,
		WALL_TILE]

GRASS_TILES = [SHORT_GRASS_TILE,
		GRASS_TILE,
		TALL_GRASS_TILE]

DIRT_TILES = [DIRT_TILE_1,
			DIRT_TILE_2,
			DIRT_TILE_3]

SAND_TILES = [SAND_TILE_1,
			SAND_TILE_2]

TILES.extend(GRASS_TILES)
TILES.extend(DIRT_TILES)
TILES.extend(SAND_TILES)


def create_tile(tile):
	_ret_tile = {}
	_ret_tile['id'] = tile['id']

	_ret_tile['items'] = []
	_ret_tile['fire'] = 0

	return _ret_tile

def get_tile(tile):
	for _tile in TILES:
		if _tile['id'] == tile['id']:
			return _tile

	raise Exception('Tile of id \'%s\' not found in TILES array.' % tile['id'])