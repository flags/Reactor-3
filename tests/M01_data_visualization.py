from libtcodpy import *

console_init_root(100, 50, 'M01 - Visualization',renderer=RENDERER_OPENGL)
console_set_custom_font('terminal8x12_gs_tc.png')
sys_set_fps(30)

SHORT_GRASS_TILE = {'id':'short_grass',
                    'icon':'.',
                    'color':(light_green,light_lime),
                    'burnable':True,
                    'cost':1}

GRASS_TILE = {'id':'grass',
              'icon':',',
              'color':(green,light_chartreuse),
              'burnable':True,
              'cost':1}

TALL_GRASS_TILE = {'id':'tall_grass',
                   'icon':';',
                   'color':(dark_green,light_green),
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

TILES = [SHORT_GRASS_TILE,GRASS_TILE,TALL_GRASS_TILE,DIRT_TILE,WALL_TILE]
MAP = []
MAP_SIZE = (100,50,5)
CAMERA_Z_LEVEL = 1
KEY = Key()
MOUSE_POS = (0,0)
MOUSE_1_DOWN = False
MOUSE = Mouse()
mouse_move(0,0)

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

MAP[3][3][2]=create_tile(GRASS_TILE)

def get_mouse_input():
	global MOUSE,MOUSE_POS,MOUSE_1_DOWN

	if MOUSE.lbutton:
		if not MOUSE_1_DOWN:
			MOUSE_1_DOWN = True
	else:
		MOUSE_1_DOWN = False

	MOUSE_POS = MOUSE.cx*2,MOUSE.cy

def get_input():
	global KEY,MOUSE

	sys_check_for_event(EVENT_KEY_PRESS|EVENT_MOUSE,KEY,MOUSE)

	get_mouse_input()

def handle_input():
	if MOUSE_1_DOWN:
		print(MOUSE_POS)
		MAP[MOUSE_POS[0]][MOUSE_POS[1]][2] = create_tile(WALL_TILE)


TIME_OF_DAY = 6
TIME_OF_DAY_MAX = 16
TIME_OF_DAY_TIMER = 1500
TIME_OF_DAY_TIMER_MAX = 1500

while not console_is_window_closed():
	get_input()
	handle_input()

	LIGHT_MAP = color_gen_map((white,
	                           light_blue,
	                           blue,
	                           light_blue,
	                           light_gray,
	                           white),[0,4,8,12,14,16])

	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			_top_tile = None
			_top_tile_z = -1
			for z in range(MAP_SIZE[2]):
				if MAP[x][y][z]:
					_top_tile = MAP[x][y][z]
					_top_tile_z = z

			_tile = get_raw_tile(_top_tile)

			console_set_char_background(None, x, y, _tile['color'][1]-LIGHT_MAP[TIME_OF_DAY])
			console_set_char_foreground(None, x, y, _tile['color'][0]-LIGHT_MAP[TIME_OF_DAY])
			console_set_char(None,x,y,_tile['icon'])

	if TIME_OF_DAY_TIMER:
		TIME_OF_DAY_TIMER-=1
	else:
		if TIME_OF_DAY<TIME_OF_DAY_MAX:
			TIME_OF_DAY+=1
		else:
			TIME_OF_DAY = 0

		TIME_OF_DAY_TIMER = TIME_OF_DAY_TIMER_MAX

	console_flush()