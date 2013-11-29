from globals import *

import libtcodpy as tcod

BLANK_TILE = {'id':'blank_tile',
				'icon': '.',
				'color':(tcod.darker_gray, tcod.black)}

SHORT_GRASS_TILE = {'id':'short_grass',
					'icon':'.',
					'color':(GRASS_GREEN_DARK, tcod.desaturated_green),
					'burnable':8,
					'cost':1}

GRASS_TILE = {'id':'grass',
			  'icon':';',
			  'color':(GRASS_GREEN, tcod.desaturated_sea),
			  'burnable':7,
			  'cost':1}

TALL_GRASS_TILE = {'id':'tall_grass',
				   'icon':'\\',
				   'color':(GRASS_GREEN, tcod.desaturated_chartreuse),
				   'burnable':6,
				   'cost':1}

DIRT_TILE = {'id':'dirt',
			 'icon':'.',
			 'color':(SAND_LIGHT,SAND),
			 'burnable':False,
			 'type': 'road',
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
			 'type': 'road',
			 'cost':2}

DIRT_TILE_2 = {'id':'dirt_2',
			 'icon':',',
			 'color':(BROWN_DARK_ALT,BROWN_DARK),
			 'burnable':False,
			 'type': 'road',
			 'cost':2}

DIRT_TILE_3 = {'id':'dirt_3',
			 'icon':'.',
			 'color':(BROWN_DARK_ALT,BROWN_DARK_ALT_2),
			 'burnable':False,
			 'type': 'road',
			 'cost':2}

WALL_TILE = {'id':'wall',
			 'icon':'#',
			 'color':(tcod.black, tcod.dark_gray),
			 'burnable':False,
			 'type': 'building',
			 'cost':-1}

BLUE_CARPET_1 = {'id':'blue_carpet_1',
			 'icon':'.',
			 'color':(tcod.desaturated_cyan, tcod.desaturated_sky),
			 'burnable':False,
			 'type': 'building',
			 'cost':-1}

BLUE_CARPET_2 = {'id':'blue_carpet_2',
			 'icon':'.',
			 'color':(tcod.desaturated_sky, tcod.desaturated_cyan),
			 'burnable':False,
			 'type': 'building',
			 'cost':-1}

SEA_CARPET_1 = {'id':'sea_carpet_1',
			 'icon':',',
			 'color':(tcod.desaturated_turquoise, tcod.desaturated_han),
			 'burnable':False,
			 'type': 'building',
			 'cost':-1}

SEA_CARPET_2 = {'id':'sea_carpet_2',
			 'icon':',',
			 'color':(tcod.desaturated_sea, tcod.desaturated_azure),
			 'burnable':False,
			 'type': 'building',
			 'cost':-1}

FIELD_TILE_1 = {'id': 'field_1',
			 'icon': '~',
			 'color': (tcod.Color(211, 181, 168), tcod.Color(210, 170, 153)),
			 'burnable': True,
			 'type': 'field',
			 'cost': 2}

FIELD_TILE_2 = {'id': 'field_2',
			 'icon': '\'',
			 'color': (tcod.Color(210, 170, 153), tcod.Color(211, 181, 168)),
			 'burnable': True,
			 'type': 'field',
			 'cost': 2}

FIELD_TILE_3 = {'id': 'field_3',
			 'icon': ';',
			 'color': (tcod.Color(211, 181, 168), tcod.Color(210, 170, 153)),
			 'burnable': True,
			 'type': 'field',
			 'cost': 2}

CONCRETE_TILE_1 = {'id':'concrete_1',
			 'icon':'.',
			 'color':(tcod.Color(130,130,130), tcod.Color(70,70,70)),
			 'burnable':False,
			 'type': 'road',
			 'cost':2}

CONCRETE_TILE_2 = {'id':'concrete_2',
			 'icon':'.',
			 'color':(tcod.Color(95,95,95), tcod.Color(62,62,62)),
			 'burnable':False,
			 'type': 'road',
			 'cost':2}

CONCRETE_FLOOR_1 = {'id':'concrete_floor_1',
			 'icon':'.',
			 'color':(tcod.Color(115,115,115), tcod.Color(100,100,100)),
			 'burnable':False,
			 'type': 'building',
			 'cost':2}

CONCRETE_FLOOR_2 = {'id':'concrete_floor_2',
			 'icon':'.',
			 'color':(tcod.Color(125,125,125), tcod.Color(110,110,110)),
			 'burnable':False,
			 'type': 'building',
			 'cost':2}

ROAD_STRIPE_1 = {'id':'road_stripe_1',
			 'icon':'.',
			 'color':(tcod.yellow, tcod.yellow),
			 'burnable':False,
			 'cost':2}

ROAD_STRIPE_2 = {'id':'road_stripe_2',
			 'icon':'.',
			 'color':(tcod.white, tcod.darker_gray),
			 'burnable':False,
			 'cost':2}

RED_BRICK_1 = {'id':'red_brick_1',
			 'icon':'#',
			 'color':(tcod.gray, tcod.dark_red),
			 'burnable':False,
			 'cost':-1}

RED_BRICK_2 = {'id':'red_brick_2',
			 'icon':'#',
			 'color':(tcod.light_gray, tcod.dark_red),
			 'burnable':False,
			 'cost':-1}

WHITE_TILE_1 = {'id':'white_tile_1',
			 'icon':',',
			 'color':(tcod.lightest_gray, tcod.lighter_gray),
			 'burnable':False,
			 'type': 'building',
			 'cost':-1}

WHITE_TILE_2 = {'id':'white_tile_2',
			 'icon':'.',
			 'color':(tcod.white, tcod.lightest_gray),
			 'burnable':False,
			 'type': 'building',
			 'cost':-1}

SMALL_TREE_STUMP_1 = {'id':'small_tree_stump_1',
			 'icon':'o',
			 'color':(tcod.brass, tcod.desaturated_sea),
			 'burnable':True,
			 'cost':-1}

SMALL_TREE_STUMP_2 = {'id':'small_tree_stump_2',
			 'icon':'o',
			 'color':(tcod.brass, tcod.desaturated_green),
			 'burnable':True,
			 'cost':-1}

WOOD_1 = {'id':'wood_1',
			 'icon':'#',
			 'color':(tcod.light_sepia, tcod.sepia),
			 'burnable':True,
			 'cost':-1}

WOOD_2 = {'id':'wood_2',
			 'icon':'#',
			 'color':(tcod.sepia, tcod.dark_sepia),
			 'burnable':True,
			 'cost':-1}

WOOD_3 = {'id':'wood_3',
			 'icon':'#',
			 'color':(tcod.sepia, tcod.dark_sepia),
			 'burnable':True,
			 'cost':-1}

LEAF_1 = {'id': 'leaf_1',
            'icon': '\'',
            'color': (tcod.darker_chartreuse, tcod.Color(54, 108, 0)),
            'burnable': True,
            'translucent': True,
            'not_solid': True}

LEAF_2 = {'id': 'leaf_2',
            'icon': '`',
            'color': (tcod.Color(64, 128, 0), tcod.Color(39, 79, 0)),
            'burnable': True,
            'translucent': True,
            'not_solid': True}

BUSH_1 = {'id': 'bush_1',
            'icon': '\'',
            'color': (tcod.darker_chartreuse, tcod.Color(54, 108, 0)),
            'burnable': True}

BUSH_2 = {'id': 'bush_2',
            'icon': '`',
            'color': (tcod.Color(64, 128, 0), tcod.Color(39, 79, 0)),
            'burnable': True}

ROOF_DARK = {'id': 'roof_dark',
            'icon': '^',
            'color': (tcod.dark_sepia, tcod.darker_sepia),
            'burnable': True}

ROOF_DARKER = {'id': 'roof_darker',
            'icon': '^',
            'color': (tcod.darker_sepia, tcod.darkest_sepia),
            'burnable': True}

ROOF_BRIGHT = {'id': 'roof_bright',
            'icon': '^',
            'color': (tcod.sepia, tcod.darker_sepia),
            'burnable': True}

ROOF_BRIGHTER = {'id': 'roof_brighter',
            'icon': '^',
            'color': (tcod.light_sepia, tcod.sepia),
            'burnable': True}

WALL_BLUE = {'id': 'wall_blue',
           'icon': '#',
           'color': (tcod.Color(47, 70, 94), tcod.Color(0, 20, 39)),
           'type': 'building',
           'burnable': False}

FLOOR_BLUE_1 = {'id': 'floor_blue',
           'icon': ',',
           'color': (tcod.white, tcod.lightest_sky),
           'type': 'building',
           'burnable': False}

FLOOR_BLUE_2 = {'id': 'floor_blue_2',
           'icon': '.',
           'color': (tcod.white, tcod.lightest_azure),
           'type': 'building',
           'burnable': False}

FLOOR_DARK_BLUE_1 = {'id': 'floor_dark_blue_1',
           'icon': '.',
           'color': (tcod.darkest_sky, tcod.darker_azure),
           'type': 'building',
           'burnable': False}

FLOOR_DARK_GREEN_1 = {'id': 'floor_dark_green_1',
           'icon': '.',
           'color': (tcod.darker_chartreuse, tcod.brass),
           'type': 'building',
           'burnable': False}

WALL_BROWN = {'id': 'wall_brown',
           'icon': '#',
           'color': (tcod.lighter_sepia, tcod.light_sepia),
           'type': 'building',
           'burnable': False}

FLOOR_BROWN_1 = {'id': 'floor_brown_1',
           'icon': '.',
           'color': (tcod.brass, tcod.Color(236, 200, 149)),#(tcod.Color(255, 216, 161), tcod.Color(236, 200, 149)),
           'type': 'building',
           'burnable': False}

#Groups
TEMP_TILES = [BLANK_TILE,
		DIRT_TILE,
		WALL_TILE,
		ROAD_STRIPE_1,
		ROAD_STRIPE_2,
		RED_BRICK_1,
		RED_BRICK_2,
		SMALL_TREE_STUMP_1]

GRASS_TILES = [SHORT_GRASS_TILE,
		GRASS_TILE,
		TALL_GRASS_TILE]

DIRT_TILES = [DIRT_TILE_1,
			DIRT_TILE_2,
			DIRT_TILE_3]

BLUE_CARPET_TILES = [BLUE_CARPET_1,
                     BLUE_CARPET_2]

SEA_CARPET_TILES = [SEA_CARPET_1,
                    SEA_CARPET_2]

TREE_STUMPS = [SMALL_TREE_STUMP_1,
               SMALL_TREE_STUMP_2]

SAND_TILES = [SAND_TILE_1,
			SAND_TILE_2]

CONCRETE_TILES = [CONCRETE_TILE_1,
			CONCRETE_TILE_2]

CONCRETE_FLOOR_TILES = [CONCRETE_FLOOR_1,
			CONCRETE_FLOOR_2]

ROAD_STRIPES = [ROAD_STRIPE_1,
                ROAD_STRIPE_2]

RED_BRICK_TILES = [RED_BRICK_1,
			RED_BRICK_2]

WHITE_TILE_TILES = [WHITE_TILE_1,
			WHITE_TILE_2]

WOOD_TILES = [WOOD_1,
              WOOD_2,
              WOOD_3]

LEAF_TILES = [LEAF_1,
              LEAF_2]

BUSH_TILES = [BUSH_1,
              BUSH_2]

ROOF_TILES = [ROOF_BRIGHTER,
              ROOF_BRIGHT,
              ROOF_DARK,
              ROOF_DARKER]

FIELD_TILES = [FIELD_TILE_1,
               FIELD_TILE_2,
               FIELD_TILE_3]

HOUSE_WALL_TILES = [WALL_BLUE, WALL_BROWN]

BLUE_FLOOR_TILES = [FLOOR_BLUE_1, FLOOR_BLUE_2]

DARK_BLUE_FLOOR_TILES = [FLOOR_DARK_BLUE_1]

DARK_GREEN_FLOOR_TILES = [FLOOR_DARK_GREEN_1]

BROWN_FLOOR_TILES = [FLOOR_BROWN_1]

def create_all_tiles():
	TEMP_TILES.extend(GRASS_TILES)
	TEMP_TILES.extend(DIRT_TILES)
	TEMP_TILES.extend(SAND_TILES)
	TEMP_TILES.extend(CONCRETE_TILES)
	TEMP_TILES.extend(CONCRETE_FLOOR_TILES)
	TEMP_TILES.extend(RED_BRICK_TILES)
	TEMP_TILES.extend(WHITE_TILE_TILES)
	TEMP_TILES.extend(TREE_STUMPS)
	TEMP_TILES.extend(WOOD_TILES)
	TEMP_TILES.extend(LEAF_TILES)
	TEMP_TILES.extend(ROOF_TILES)
	TEMP_TILES.extend(HOUSE_WALL_TILES)
	TEMP_TILES.extend(BLUE_FLOOR_TILES)
	TEMP_TILES.extend(DARK_BLUE_FLOOR_TILES)
	TEMP_TILES.extend(DARK_GREEN_FLOOR_TILES)
	TEMP_TILES.extend(BROWN_FLOOR_TILES)
	TEMP_TILES.extend(FIELD_TILES)
	TEMP_TILES.extend(BLUE_CARPET_TILES)
	TEMP_TILES.extend(SEA_CARPET_TILES)
	TEMP_TILES.extend(BUSH_TILES)

	for tile in TEMP_TILES:
		TILES[tile['id']] = tile

def create_tile(tile):
	_ret_tile = {}
	_ret_tile['id'] = tile['id']

	return _ret_tile

def get_raw_tile(tile):
	return TILES[tile['id']]

def get_tile(pos):
	return WORLD_INFO['map'][pos[0]][pos[1]][pos[2]]

def flag(tile, flag, value):
	tile['flags'][flag] = value
	
	return value

def get_flag(tile, flag):
	if not flag in tile['flags']:
		return False
	
	return tile['flags'][flag]
