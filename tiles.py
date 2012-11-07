from libtcodpy import *
from globals import *

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
             'color':(gray,gray),
             'burnable':False,
             'cost':2}

WALL_TILE = {'id':'wall',
             'icon':'#',
             'color':(black,gray),
             'burnable':False,
             'cost':-1}

TILES = [SHORT_GRASS_TILE,
         GRASS_TILE,
         TALL_GRASS_TILE,
         DIRT_TILE,
         WALL_TILE]

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

	raise Exception