"""Reactor 3"""

from libtcodpy import *
from globals import *
from inputs import *
from player import *
from tiles import *

import graphics as gfx
import maputils
import worldgen
import mainmenu
import drawing
import logging
import weapons
import effects
import numbers
import bullets
import random
import menus
import logic
import items
import life
import time
import maps
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('[%(asctime)s-%(levelname)s] %(message)s',datefmt='%H:%M:%S %m/%d/%y')
ch = logging.StreamHandler()
ch.setFormatter(console_formatter)
logger.addHandler(ch)

#TODO: Replace with "module_sanity_check"
#Optional Cython-compiled modules
try:
	import render_map
	import render_los
	
	if render_map.VERSION == MAP_RENDER_VERSION:
		CYTHON_ENABLED = True
	else:
		CYTHON_ENABLED = False
		logging.warning('[Cython] render_map is out of date!')
		logging.warning('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')
	
except ImportError, e:
	CYTHON_ENABLED = False
	logging.warning('[Cython] ImportError with module: %s' % e)
	logging.warning('[Cython] Certain functions can run faster if compiled with Cython.')
	logging.warning('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')

gfx.log(WINDOW_TITLE)

try:
	MAP = maps.load_map('map1.dat')
except IOError:
	MAP = maps.create_map()
	maps.save_map(MAP)

create_all_tiles()
maps.update_chunk_map(MAP)
maps.smooth_chunk_map()
maps.generate_reference_maps()
gfx.init_libtcod()

PLACING_TILE = WALL_TILE

def move_camera(pos,scroll=False):
	CAMERA_POS[0] = numbers.clip(pos[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0]-MAP_WINDOW_SIZE[0])
	CAMERA_POS[1] = numbers.clip(pos[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1]-MAP_WINDOW_SIZE[1])
	CAMERA_POS[2] = pos[2]

def draw_targeting():
	if SETTINGS['controlling'] and SETTINGS['controlling']['targeting']:
		
		SELECTED_TILES[0] = []
		for pos in drawing.diag_line(SETTINGS['controlling']['pos'],SETTINGS['controlling']['targeting']):
			SELECTED_TILES[0].append((pos[0],pos[1],SETTINGS['controlling']['pos'][2]))

LIGHTS.append({'x': 12,'y': 20,'z': 2,'brightness': 50.0})

SETTINGS['draw z-levels below'] = True
SETTINGS['draw z-levels above'] = True

life.initiate_life('Human')

items.initiate_item('white_shirt')
items.initiate_item('sneakers')
items.initiate_item('leather_backpack')
items.initiate_item('blue_jeans')
items.initiate_item('glock')
items.initiate_item('9x19mm_mag')
items.initiate_item('9x19mm_round')
items.initiate_item('radio')

items.create_item('leather backpack',position=[40,50,2])
items.create_item('glock',position=[40,35,2])

#while 1:
#	get_input()
#	mainmenu.draw_main_menu()
#	
#	if INPUT['s']:
#		break
#	elif INPUT['o']:
#		if mainmenu.MENU[0] == mainmenu.MAIN_MENU_TEXT:
#			mainmenu.MENU[0] = mainmenu.WORLD_INFO_TEXT
#		
#	elif INPUT['q']:
#		if mainmenu.MENU[0] == mainmenu.MAIN_MENU_TEXT:
#			SETTINGS['running'] = False
#			break
#		else:
#			mainmenu.MENU[0] = mainmenu.MAIN_MENU_TEXT

worldgen.generate_world(MAP, life=2, simulate_ticks=1)

CURRENT_UPS = UPS

while SETTINGS['running']:
	get_input()
	handle_input()
	_played_moved = False

	while life.get_highest_action(SETTINGS['controlling']):
		logic.tick_all_objects(MAP)
		_played_moved = True
		
		if CURRENT_UPS:
			CURRENT_UPS-=1
		else:
			CURRENT_UPS = UPS
			break
	
	if not _played_moved:
		logic.tick_all_objects(MAP)
	
	draw_targeting()
	
	if CYTHON_ENABLED:
		render_map.render_map(MAP)
	else:
		maps.render_map(MAP)
	
	#maps.render_lights(MAP)
	items.draw_items()
	bullets.draw_bullets()
	
	move_camera(SETTINGS['following']['pos'])
	life.draw_life()
	
	if SETTINGS['controlling']['encounters']:
		LOS_BUFFER[0] = maps._render_los(MAP, SETTINGS['controlling']['pos'], cython=CYTHON_ENABLED)
	else:
		LOS_BUFFER[0] = maps._render_los(MAP, SETTINGS['following']['pos'], cython=CYTHON_ENABLED)
	
	if SETTINGS['controlling']['dead']:
		gfx.fade_to_white(FADE_TO_WHITE[0])
		_col = 255-int(round(FADE_TO_WHITE[0]))*2
		
		if _col<0:
			_col = 0
		
		_string = 'You die.'
		
		gfx.blit_string(MAP_WINDOW_SIZE[0]/2-(len(_string)/2),
			MAP_WINDOW_SIZE[1]/2,
			_string,
			console=MAP_WINDOW,
			fore_color=Color(255,_col,_col),
			back_color=Color(255-_col,255-_col,255-_col),
			flicker=0)
		FADE_TO_WHITE[0] += 0.9
	
	logic.tick_world()
	life.draw_life_info()
	menus.align_menus()
	menus.draw_menus()
	logic.draw_encounter()
	#gfx.draw_effects()
	gfx.draw_message_box()
	gfx.draw_status_line()
	gfx.draw_console()
	gfx.start_of_frame()
	gfx.end_of_frame_reactor3()
	gfx.end_of_frame()
