from libtcodpy import *

console_init_root(100, 50, 'M01 - Visualization',renderer=RENDERER_OPENGL)
console_set_custom_font('terminal12x12_gs_ro.png',FONT_LAYOUT_ASCII_INCOL)
sys_set_fps(30)

SHORT_GRASS_TILE = {'id':'short_grass',
                    'icon':'.',
                    'color':(light_green,Color(0,230,0)),
                    'burnable':True,
                    'cost':1}

GRASS_TILE = {'id':'grass',
              'icon':',',
              'color':(green,Color(0,210,0)),
              'burnable':True,
              'cost':1}

TALL_GRASS_TILE = {'id':'tall_grass',
                   'icon':';',
                   'color':(dark_green,Color(0,205,0)),
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
CURSOR_POS = [0,0]
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

	MOUSE_POS = MOUSE.x//16,MOUSE.y//16

def get_input():
	global KEY,MOUSE,CURSOR_POS

	sys_check_for_event(EVENT_KEY_PRESS|EVENT_MOUSE,KEY,MOUSE)

	if KEY.vk == KEY_UP:
		if CURSOR_POS[1]>0: CURSOR_POS[1]-=1
	elif KEY.vk == KEY_DOWN:
		if CURSOR_POS[1]<MAP_SIZE[1]-1: CURSOR_POS[1]+=1

	if KEY.vk == KEY_LEFT:
		if CURSOR_POS[0]>0: CURSOR_POS[0]-=1
	elif KEY.vk == KEY_RIGHT:
		if CURSOR_POS[0]<MAP_SIZE[0]-1: CURSOR_POS[0]+=1

	if KEY.vk == KEY_SPACE:
		MAP[CURSOR_POS[0]][CURSOR_POS[1]][2] = create_tile(WALL_TILE)

	get_mouse_input()

def handle_input():
	global MOUSE_POS
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

			console_set_char_background(None, x, y, _tile['color'][1])
			console_set_char_foreground(None, x, y, _tile['color'][0])
			console_set_char(None,x,y,_tile['icon'])

	if TIME_OF_DAY_TIMER:
		TIME_OF_DAY_TIMER-=1
	else:
		if TIME_OF_DAY<TIME_OF_DAY_MAX:
			TIME_OF_DAY+=1
		else:
			TIME_OF_DAY = 0

		TIME_OF_DAY_TIMER = TIME_OF_DAY_TIMER_MAX

	console_set_char_background(None,CURSOR_POS[0],CURSOR_POS[1],black)
	console_set_char(None,CURSOR_POS[0],CURSOR_POS[1],'X')

	console_flush()