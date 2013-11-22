"""Terraform - World editor for Reactor 3"""

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('[%(asctime)s-%(levelname)s] %(message)s',datefmt='%H:%M:%S %m/%d/%y')
ch = logging.StreamHandler()
ch.setFormatter(console_formatter)
logger.addHandler(ch)

from libtcodpy import *
from globals import *
from inputs import *
from tiles import *

import graphics as gfx

import language
import maputils
import profiles
import weather
import numbers
import random
import mapgen
import items
import zones
import menus
import time
import maps
import sys
import smp

import cProfile

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

def move_camera(pos, scroll=False):
	_orig_pos = CAMERA_POS[:]
	CAMERA_POS[0] = numbers.clip(pos[0]-(WINDOW_SIZE[0]/2),0,MAP_SIZE[0]-WINDOW_SIZE[0])
	CAMERA_POS[1] = numbers.clip(pos[1]-(WINDOW_SIZE[1]/2),0,MAP_SIZE[1]-WINDOW_SIZE[1])
	CAMERA_POS[2] = pos[2]
	
	if not _orig_pos == CAMERA_POS:
		gfx.refresh_view('map')
	elif SETTINGS['controlling'] and not alife.brain.get_flag(LIFE[SETTINGS['controlling']], 'redraw') == pos:
		gfx.refresh_view('map')

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	if gfx.window_is_closed():
		SETTINGS['running'] = False
		
		return True
	
	elif INPUT['\x1b'] or INPUT['q']:
		if not ACTIVE_MENU['menu'] == -1 and not SETTINGS['running'] == 1:
			ACTIVE_MENU['menu'] = -1
			
			return True
			
		SETTINGS['running'] = False
		
		return True
	
	elif INPUT['-']:
		if SETTINGS['draw console']:
			SETTINGS['draw console'] = False
		else:
			SETTINGS['draw console'] = True
	
	elif SETTINGS['draw console']:
		return

	elif INPUT['up']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.move_up(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR_POS[1] -= SETTINGS['cursor speed']

	elif INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.move_down(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR_POS[1] += SETTINGS['cursor speed']

	elif INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR_POS[0] += SETTINGS['cursor speed']

	elif INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR_POS[0] -= SETTINGS['cursor speed']

	elif INPUT[' ']:
		pass
	
	elif INPUT['m']:
		gfx.refresh_view('map')
	
	elif INPUT['n']:
		SUN_POS[2] -= 1
	
	elif INPUT['o']:
		pass
	
	elif INPUT['\r']:
		if ACTIVE_MENU['menu'] == -1:
			return False
		
		menus.item_selected(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		ACTIVE_MENU['menu'] = -1
	
	elif INPUT['\t']:
		pass
	
	elif INPUT['f']:
		#_matching = MAP[MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]].rpartition('_')[0]
		_matching = 'grass'
		
		#SELECTED_TILES[0] = maps.flood_select_by_tile(MAP,
		#	_matching,
		#	(MAP_CURSOR[0],MAP_CURSOR[1],CAMERA_POS[2]))

	elif INPUT['c']:
		CURSOR_POS[0] = MAP_SIZE[0]/2
		CURSOR_POS[1] = MAP_SIZE[1]/2

	elif INPUT['r']:
		language.load_strings()
		WORLD_INFO['lights'] = []
		
		for key in ITEMS.keys():
			del ITEMS[key]
		
		gfx.title('Generating...')
		reload(mapgen)
		mapgen.generate_map(size=(250, 250, 10),
		                    towns=1,
		                    factories=0,
		                    outposts=0,
		                    forests=1,
		                    skip_zoning=True,
		                    skip_chunking=True,
		                    hotload=True)
		gfx.refresh_view('map')

	elif INPUT['l']:
		SUN_BRIGHTNESS[0] += 4
	
	elif INPUT['k']:
		SUN_BRIGHTNESS[0] -= 4

	elif INPUT['1']:
		CAMERA_POS[2] = 1
		gfx.refresh_view('map')

	elif INPUT['2']:
		CAMERA_POS[2] = 2
		gfx.refresh_view('map')

	elif INPUT['3']:
		CAMERA_POS[2] = 3
		gfx.refresh_view('map')

	elif INPUT['4']:
		CAMERA_POS[2] = 4
		gfx.refresh_view('map')

	elif INPUT['5']:
		CAMERA_POS[2] = 5
		gfx.refresh_view('map')
	
	elif INPUT['6']:
		CAMERA_POS[2] = 6
		gfx.refresh_view('map')
	
	elif INPUT['7']:
		CAMERA_POS[2] = 7
		gfx.refresh_view('map')
	
	elif INPUT['8']:
		CAMERA_POS[2] = 8
		gfx.refresh_view('map')
	
	elif INPUT['9']:
		CAMERA_POS[2] = 9
		gfx.refresh_view('map')
	
	elif INPUT['0']:
		CAMERA_POS[2] = 0
		gfx.refresh_view('map')

def menu_item_selected(entry):
	menus.delete_active_menu()
	gfx.title('Loading...')
	maps.load_map(entry['key'])
	items.reload_all_items()
	weather.change_weather()
	LOS_BUFFER[0] = numpy.ones((WINDOW_SIZE[1], WINDOW_SIZE[0]))
	WORLD_INFO['real_time_of_day'] = 2000
	
	SETTINGS['running'] = 2

def menu_align():
	for menu in MENUS:
		if not MENUS.index(menu):
			continue
		
		_prev_menu = MENUS[MENUS.index(menu)-1]
		_size = _prev_menu['settings']['position'][1]+_prev_menu['settings']['size'][1]
		
		menu['settings']['position'][1] = _size

def create_maps_menu():
	_menu_items = []
	
	for map_file in profiles.get_maps():
		_menu_items.append(menus.create_item('single', map_file, None))
	
	if not _menu_items:
		logging.error('No maps found.')
		sys.exit(1)
	
	_m = menus.create_menu(title='Maps',
		menu=_menu_items,
		padding=(1,1),
		position=(0, 0),
		on_select=menu_item_selected,
	    format_str='$k')
	
	menus.activate_menu(_m)
	menu_align()

def map_selection():
	menus.align_menus()
	menus.draw_menus()
	
	gfx.end_of_frame()

def terraform():
	move_camera(CURSOR_POS)
	render_map.render_map(WORLD_INFO['map'], view_size=WINDOW_SIZE)
	maps.render_lights(size=WINDOW_SIZE)
	items.draw_items()
	menus.align_menus()
	menus.draw_menus()
	
	gfx.start_of_frame()
	gfx.end_of_frame()

def main():
	while SETTINGS['running']:
		get_input()
		handle_input()
		
		#Show list of maps if not passed directly
		if SETTINGS['running'] == 1:
			if menus.get_menu_by_name('Maps')>-1:
				map_selection()
			else:
				create_maps_menu()
		
		elif SETTINGS['running'] == 2:
			terraform()
		
if __name__ == '__main__':
	create_all_tiles()
	items.initiate_all_items()
	
	gfx.init_libtcod(map_view_size=WINDOW_SIZE)
	gfx.prepare_terraform_views()
	gfx.log(WINDOW_TITLE)
	
	sys_set_fps(FPS_TERRAFORM)
	console_set_keyboard_repeat(200, 30)
	
	main()
