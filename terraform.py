"""Terraform - World editor for Reactor 3"""

import logging
import importlib

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
import bad_numbers
import mapgen
import items
import zones
import menus
import maps
import smp

import cProfile
import random
import time
import sys


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
	
except ImportError as e:
	CYTHON_ENABLED = False
	logging.warning('[Cython] ImportError with module: %s' % e)
	logging.warning('[Cython] Certain functions can run faster if compiled with Cython.')
	logging.warning('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')

def pre_setup_world():
	language.load_strings()
	create_all_tiles()
	WORLD_INFO['lights'] = []

	for key in list(ITEMS.keys()):
		del ITEMS[key]

def post_setup_world():
	items.reload_all_items()
	weather.change_weather()
	maps.create_position_maps()
	
	WORLD_INFO['real_time_of_day'] = WORLD_INFO['length_of_day']//2

def regenerate_world(build_test=False):
	gfx.title('Generating...')
	
	importlib.reload(mapgen)
	
	if build_test:
		mapgen.create_buildings()
	
	pre_setup_world()
	
	try:
		mapgen.generate_map(towns=1,
			                factories=0,
			                outposts=2,
			                forests=1,
			                skip_zoning=True,
			                skip_chunking=True,
			                hotload=True,
		                     build_test=build_test)
	except:
		import traceback
		traceback.print_exc()
		SETTINGS['running'] = 1
		
		return False
	
	post_setup_world()
	gfx.refresh_view('map')
	
	return True

def move_camera(pos, scroll=False):
	_orig_pos = CAMERA_POS[:]
	CAMERA_POS[0] = bad_numbers.clip(pos[0]-(WINDOW_SIZE[0]//2),0,MAP_SIZE[0]-WINDOW_SIZE[0])
	CAMERA_POS[1] = bad_numbers.clip(pos[1]-(WINDOW_SIZE[1]//2),0,MAP_SIZE[1]-WINDOW_SIZE[1])
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
		menus.activate_menu_by_name('Buildings')
	
	elif INPUT['n']:
		for alife in LIFE:
			life.memory(alife, 'focus_on_chunk', chunk_key=life.get_current_chunk_id(LIFE[SETTINGS['controlling']]))
	
	elif INPUT['\r']:
		if ACTIVE_MENU['menu'] == -1:
			return False
		
		menus.item_selected(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		ACTIVE_MENU['menu'] = -1
	
	elif INPUT['\t']:
		pass

	elif INPUT['c']:
		CURSOR_POS[0] = MAP_SIZE[0]//2
		CURSOR_POS[1] = MAP_SIZE[1]//2

	elif INPUT['m']:
		if SETTINGS['running'] == 2:
			gfx.add_view_to_scene_by_name('chunk_map')
			gfx.set_active_view('chunk_map')
			
			SETTINGS['running'] = 3
		elif SETTINGS['running'] == 3:
			gfx.remove_view_from_scene_by_name('chunk_map')
			gfx.set_active_view('map')
			SETTINGS['running'] = 2

	elif INPUT['r']:
		if regenerate_world():
			SETTINGS['running'] = 2

	elif INPUT['s']:
		items.save_all_items()
		
		gfx.title('Generating Chunk Map')
		maps.update_chunk_map()
		
		gfx.title('Zoning...')
		zones.create_zone_map()
		
		gfx.title('Pathing...')
		mapgen.create_path_map()
		
		gfx.title('Saving...')
		maps.save_map(str(time.time()), only_cached=False)
		items.reload_all_items()

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
	if MENUS:
		menus.delete_active_menu()
	
	gfx.title('Loading...')
	
	pre_setup_world()
	maps.load_map(entry['key'])
	post_setup_world()
	
	SETTINGS['running'] = 2

def building_type_selected(entry):
	gfx.title('Loading...')
	
	#pre_setup_world()
	regenerate_world(build_test=entry['key'])
	#mapgen.generate_map(build_test=entry['key'], skip_chunking=True, skip_zoning=True)
	#post_setup_world()
	gfx.refresh_view('map')
	
	SETTINGS['running'] = 2

def menu_align():
	for menu in MENUS:
		if not MENUS.index(menu):
			continue
		
		_prev_menu = MENUS[MENUS.index(menu)-1]
		_size = _prev_menu['settings']['position'][1]+_prev_menu['settings']['size'][1]
		
		menu['settings']['position'][1] = _size

def create_maps_menu(build_test):
	_menu_items = []
	
	if build_test:
		for building_type in mapgen.BUILDINGS:
			_menu_items.append(menus.create_item('single', building_type, None))
		
		_m = menus.create_menu(title='Buildings',
			                  menu=_menu_items,
			                  padding=(1,1),
			                  position=(0, 0),
			                  on_select=building_type_selected,
			                  format_str='$k')
	else:
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
	maps.render_lights(size=WINDOW_SIZE, show_weather=False)
	items.draw_all_items()
	menus.align_menus()
	menus.draw_menus()
	gfx.start_of_frame()
	gfx.end_of_frame()

def chunk_map():
	move_camera(CURSOR_POS)
	maps.draw_chunk_map()
	gfx.start_of_frame()
	gfx.end_of_frame()

def main():
	if not '--select' in sys.argv and not '--test' in sys.argv:
		if regenerate_world():
			SETTINGS['running'] = 2
	
	while SETTINGS['running']:
		get_input()
		handle_input()
		
		#Show list of maps if not passed directly
		if SETTINGS['running'] == 1:
			if menus.get_menu_by_name('Maps')>-1 or menus.get_menu_by_name('Buildings')>-1:
				map_selection()
			else:
				create_maps_menu('--test' in sys.argv)
		
		elif SETTINGS['running'] == 2:
			terraform()
		
		elif SETTINGS['running'] == 3:
			chunk_map()
		
if __name__ == '__main__':
	create_all_tiles()
	items.initiate_all_items()
	
	gfx.init_libtcod(map_view_size=WINDOW_SIZE)
	gfx.prepare_terraform_views()
	gfx.log(WINDOW_TITLE)
	
	sys_set_fps(FPS_TERRAFORM)
	
	mapgen.create_buildings()
	
	main()
