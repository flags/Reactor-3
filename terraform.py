"""Terraform - World editor for Reactor 3"""
from libtcodpy import *
from globals import *
from inputs import *
from tiles import *
import graphics as gfx
import cProfile
import maputils
import logging
import prefabs
import random
import menus
import time
import maps
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('[%(asctime)s-%(levelname)s] %(message)s',datefmt='%H:%M:%S %m/%d/%y')
ch = logging.StreamHandler()
ch.setFormatter(console_formatter)
logger.addHandler(ch)

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


gfx.init_libtcod(terraform=True)
create_all_tiles()

#TODO: Scroll speed
console_set_keyboard_repeat(200, 30)
sys_set_fps(FPS_TERRAFORM)

PLACING_TILE = WALL_TILE

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	if gfx.window_is_closed():
		RUNNING = False
		
		return True
	
	elif INPUT['\x1b']:
		if not ACTIVE_MENU['menu'] == -1:
			ACTIVE_MENU['menu'] = -1
			
			return True
			
		RUNNING = False
		
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
			MENUS[ACTIVE_MENU['menu']]['index'] = menus.find_item_before(MENUS[ACTIVE_MENU['menu']],index=MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR[1] -= 1
			
			if CAMERA_POS[1]<CAMERA_POS[1]+MAP_WINDOW_SIZE[1]/2 and CAMERA_POS[1]>0:
				CAMERA_POS[1] -= 1

	elif INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			MENUS[ACTIVE_MENU['menu']]['index'] = menus.find_item_after(MENUS[ACTIVE_MENU['menu']],index=MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR[1] += 1

			if CURSOR[1]-CAMERA_POS[1]>MAP_WINDOW_SIZE[1]/2:
				CAMERA_POS[1] += 1

	elif INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR[0] += 1

			if CURSOR[0]-CAMERA_POS[0]>=MAP_WINDOW_SIZE[0]/2:
				CAMERA_POS[0]+=1

	elif INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			CURSOR[0] -= 1

			if CAMERA_POS[0]<CAMERA_POS[0]+MAP_WINDOW_SIZE[0]/2 and\
					CAMERA_POS[0]>0:
				CAMERA_POS[0] -= 1

	elif INPUT[' ']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(PLACING_TILE)
	
	elif INPUT['m']:
		SUN_POS[0] += 1
		SUN_POS[1] += 1
	
	elif INPUT['n']:
		SUN_POS[2] -= 1
	
	elif INPUT['o']:
		if not ACTIVE_MENU['menu'] == -1:
			ACTIVE_MENU['menu'] = -1
			
			return True
		
		menus.activate_menu(0)
	
	elif INPUT['\r']:
		if ACTIVE_MENU['menu'] == -1:
			return False
		
		menus.item_selected(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		ACTIVE_MENU['menu'] = -1
	
	elif INPUT['q']:
		_current_index = TILES.index(PLACING_TILE)-1
		
		if _current_index<0:
			_current_index = 0
		
		PLACING_TILE = TILES[_current_index]
			
	elif INPUT['w']:
		_current_index = TILES.index(PLACING_TILE)+1
		
		if _current_index>=len(TILES):
			_current_index = len(TILES)-1
		
		PLACING_TILE = TILES[_current_index]
	
	#if INPUT['f']:
	#	SELECTED_TILES.extend(maps.flood_select_by_tile(MAP,PLACING_TILE,(CURSOR[0],CURSOR[1],CAMERA_POS[2])))

	elif INPUT['c']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(GRASS_TILES))

	elif INPUT['d']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = None
	
	elif INPUT['a']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(SAND_TILES))
	
	elif INPUT['b']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(RED_BRICK_TILES))

	elif INPUT['g']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(CONCRETE_FLOOR_TILES))
	
	elif INPUT['s']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(DIRT_TILES))
	
	elif INPUT['z']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(CONCRETE_TILES))

	elif INPUT['l']:
		SUN_BRIGHTNESS[0] += 4
	
	elif INPUT['k']:
		SUN_BRIGHTNESS[0] -= 4

	elif INPUT['1']:
		CAMERA_POS[2] = 1

	elif INPUT['2']:
		CAMERA_POS[2] = 2

	elif INPUT['3']:
		CAMERA_POS[2] = 3

	elif INPUT['4']:
		CAMERA_POS[2] = 4

	elif INPUT['5']:
		CAMERA_POS[2] = 5
	
	elif INPUT['6']:
		CAMERA_POS[2] = 6
	
	elif INPUT['7']:
		CAMERA_POS[2] = 7
	
	elif INPUT['8']:
		CAMERA_POS[2] = 8

def menu_item_selected(entry):
	global RUNNING
	value = entry['values'][entry['value']]
	
	if value == 'Save':
		maps.save_map('map1.dat',MAP)
	elif value == 'Exit':
		RUNNING = False

def menu_item_changed(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Blit z-level below':
		if value == 'On':
			SETTINGS['draw z-levels below'] = True
		elif value == 'Off':
			SETTINGS['draw z-levels below'] = False
	
	elif key == 'Blit z-level above':
		if value == 'On':
			SETTINGS['draw z-levels above'] = True
		elif value == 'Off':
			SETTINGS['draw z-levels above'] = False
	
	elif key == 'Draw lights':
		if value == 'On':
			SETTINGS['draw lights'] = True
		elif value == 'Off':
			maps.reset_lights()
			SETTINGS['draw lights'] = False

def menu_align():
	for menu in MENUS:
		if not MENUS.index(menu):
			continue
		
		_prev_menu = MENUS[MENUS.index(menu)-1]
		_size = _prev_menu['settings']['position'][1]+_prev_menu['settings']['size'][1]
		
		menu['settings']['position'][1] = _size

_menu_items = []
_menu_items.append(menus.create_item('title','Tile Operations',None,enabled=False))
_menu_items.append(menus.create_item('single','^','Move selected up'))
_menu_items.append(menus.create_item('single','v','Move selected down', enabled=False))
_menu_items.append(menus.create_item('single','Del','Delete all'))
_menu_items.append(menus.create_item('spacer','=',None,enabled=False))

_menu_items.append(menus.create_item('title','Map Utils',None,enabled=False))
_menu_items.append(menus.create_item('single','Width',MAP_SIZE[0]))
_menu_items.append(menus.create_item('single','Height',MAP_SIZE[1]))
_menu_items.append(menus.create_item('single','Depth',MAP_SIZE[2]))
_menu_items.append(menus.create_item('spacer','=',None,enabled=False))

_menu_items.append(menus.create_item('title','View',None,enabled=False))
_menu_items.append(menus.create_item('list','Blit z-level below',['Off','On']))
_menu_items.append(menus.create_item('list','Blit z-level above',['On','Off']))
_menu_items.append(menus.create_item('list','Draw lights',['On','Off']))
_menu_items.append(menus.create_item('spacer','=',None,enabled=False))

_menu_items.append(menus.create_item('title','General',None,enabled=False))
_menu_items.append(menus.create_item('list','S','Save'))
_menu_items.append(menus.create_item('list','L','Load'))
_menu_items.append(menus.create_item('list','E','Exit'))

menus.create_menu(title='Options',
	menu=_menu_items,
	padding=(1,1),
	position=(MAP_WINDOW_SIZE[0],0),
	on_select=menu_item_selected,
	on_change=menu_item_changed)

menu_align()

#MAP = maputils.resize_map(MAP,(500,500,5))
LIGHTS.append({'x': 40,'y': 30,'brightness': 20.0})
LIGHTS.append({'x': 20,'y': 25,'brightness': 20.0})

test_prefab = prefabs.create_new_prefab((10,10,3))

def main():
	while RUNNING:
		get_input()
		handle_input()

		if CYTHON_ENABLED:
			render_map.render_map(MAP)
		else:
			maps.render_map(MAP)
		
		#maps.render_lights()
		
		#LIGHTS[0]['x'] = CURSOR[0]
		#LIGHTS[0]['y'] = CURSOR[1]

		gfx.draw_cursor(PLACING_TILE)
		gfx.draw_all_tiles()
		gfx.draw_bottom_ui_terraform()
		gfx.draw_selected_tile_in_item_window(TILES.keys().index(PLACING_TILE['id']))
		menus.draw_menus()
		gfx.draw_console()
		prefabs.draw_prefab(test_prefab)
		gfx.start_of_frame()
		gfx.start_of_frame_terraform()
		gfx.end_of_frame_terraform()
		gfx.end_of_frame()

if '--profile' in sys.argv:
	logging.info('Profiling. Exit when completed.')
	cProfile.run('main()','profile.dat')
else:
	main()

#TODO: write this into the utility
#maputils.resize_map(MAP,(MAP_SIZE[0],MAP_SIZE[1],MAP_SIZE[2]+5))

maps.save_map('map1.dat',MAP)
