"""Terraform - World editor for Reactor 3"""
from libtcodpy import *
from globals import *
from inputs import *
from tiles import *
import graphics as gfx
import maputils
import logging
import random
import menus
import time
import maps
import sys

#Optional Cython-compiled modules
try:
	import render_map
	CYTHON_ENABLED = True
except ImportError, e:
	CYTHON_ENABLED = False
	print '[Cython] ImportError with module: %s' % e
	print '[Cython] Certain functions can run faster if compiled with Cython.'
	print '[Cython] Run \'python compile_cython_modules.py build_ext --inplace\''

gfx.log(WINDOW_TITLE)

try:
	MAP = maps.load_map('map1.dat')
except IOError:
	MAP = maps.create_map()
	maps.save_map(MAP)

gfx.init_libtcod()
sys_set_fps(FPS_TERRAFORM)

PLACING_TILE = WALL_TILE

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	"""Parses input."""
	if gfx.window_is_closed() or INPUT['\x1b']:
		RUNNING = False
	
	if INPUT['-']:
		if SETTINGS['draw console']:
			SETTINGS['draw console'] = False
		else:
			SETTINGS['draw console'] = True
	
	if SETTINGS['draw console']:
		return

	if INPUT['up']:
		if not ACTIVE_MENU['menu'] == -1:
			if ACTIVE_MENU['index']>0:
				ACTIVE_MENU['index'] -= 1
			else:
				ACTIVE_MENU['index'] = len(MENUS[ACTIVE_MENU['menu']]['menu'])-1
		else:
			CURSOR[1] -= 1
			
			if CAMERA_POS[1]<CAMERA_POS[1]+MAP_WINDOW_SIZE[1]/2 and CAMERA_POS[1]>0:
				CAMERA_POS[1] -= 1

	if INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			if ACTIVE_MENU['index']<len(MENUS[ACTIVE_MENU['menu']]['menu'])-1:
				ACTIVE_MENU['index'] += 1
			else:
				ACTIVE_MENU['index'] = 0
		else:
			CURSOR[1] += 1

			if CURSOR[1]-CAMERA_POS[1]>MAP_WINDOW_SIZE[1]/2:
				CAMERA_POS[1] += 1

	if INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],ACTIVE_MENU['index'])
		else:
			CURSOR[0] += 1

			if CURSOR[0]-CAMERA_POS[0]>=MAP_WINDOW_SIZE[0]/2:
				CAMERA_POS[0]+=1

	if INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],ACTIVE_MENU['index'])
		else:
			CURSOR[0] -= 1

			if CAMERA_POS[0]<CAMERA_POS[0]+MAP_WINDOW_SIZE[0]/2 and\
					CAMERA_POS[0]>0:
				CAMERA_POS[0] -= 1

	if INPUT[' ']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(PLACING_TILE)
	
	if INPUT['m']:
		SUN_POS[0] += 1
		SUN_POS[1] += 1
		
		print SUN_POS
	
	if INPUT['n']:
		SUN_POS[2] -= 1
		
		print SUN_POS
	
	if INPUT['o']:
		if ACTIVE_MENU['menu'] < len(MENUS):
			ACTIVE_MENU['menu'] += 1
			ACTIVE_MENU['index'] = 0
	
	if INPUT['j']:
		if ACTIVE_MENU['menu'] > -1:
			menus.item_selected(MENUS[ACTIVE_MENU['menu']],ACTIVE_MENU['index'])
		
		ACTIVE_MENU['menu'] = -1
	
	if INPUT['q']:
		_current_index = TILES.index(PLACING_TILE)-1
		
		if _current_index<0:
			_current_index = 0
		
		PLACING_TILE = TILES[_current_index]
			
	if INPUT['w']:
		_current_index = TILES.index(PLACING_TILE)+1
		
		if _current_index>=len(TILES):
			_current_index = len(TILES)-1
		
		PLACING_TILE = TILES[_current_index]
	
	#if INPUT['f']:
	#	SELECTED_TILES.extend(maps.flood_select_by_tile(MAP,PLACING_TILE,(CURSOR[0],CURSOR[1],CAMERA_POS[2])))

	if INPUT['c']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(GRASS_TILES))

	if INPUT['d']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = None
	
	if INPUT['a']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(SAND_TILES))
	
	if INPUT['b']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(RED_BRICK_TILES))

	if INPUT['g']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(CONCRETE_FLOOR_TILES))
	
	if INPUT['s']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(DIRT_TILES))
	
	if INPUT['z']:
		MAP[CURSOR[0]][CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(CONCRETE_TILES))

	if INPUT['l']:
		SUN_BRIGHTNESS[0] += 4
	
	if INPUT['k']:
		SUN_BRIGHTNESS[0] -= 4

	if INPUT['1']:
		CAMERA_POS[2] = 1

	if INPUT['2']:
		CAMERA_POS[2] = 2

	if INPUT['3']:
		CAMERA_POS[2] = 3

	if INPUT['4']:
		CAMERA_POS[2] = 4

	if INPUT['5']:
		CAMERA_POS[2] = 5

def menu_item_selected(key,value):
	if value == 'Save':
		maps.save_map(MAP)

def options_menu_item_changed(key,value):
	if key == 'Blit z-level below':
		if value == 'On':
			SETTINGS['draw z-levels below'] = True
		elif value == 'Off':
			SETTINGS['draw z-levels below'] = False
	
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
_menu_items.append(menus.create_item('single','^','Move selected up'))
_menu_items.append(menus.create_item('single','v','Move selected down'))
_menu_items.append(menus.create_item('single','Del','Delete all'))

menus.create_menu(title='Tile Operations',
	menu=_menu_items,
	padding=(1,1),
	position=(MAP_WINDOW_SIZE[0],0),
	on_select=menu_item_selected)

#menus.create_menu(title='Map Utils',
	#menu={'Width': MAP_SIZE[0],
	#'Height': MAP_SIZE[1],
	#'Depth': MAP_SIZE[2]},
	#padding=(1,1),
	#position=(MAP_WINDOW_SIZE[0],0),
	#on_select=menu_item_selected)

_menu_items = []
_menu_items.append(menus.create_item('list','Blit z-level below',['Off','On']))
_menu_items.append(menus.create_item('list','Draw lights',['On','Off']))

menus.create_menu(title='View',
	menu=_menu_items,
	padding=(1,1),
	position=(MAP_WINDOW_SIZE[0],0),
	on_select=menu_item_selected,
	on_change=options_menu_item_changed)

#menus.create_menu(title='General',
	#menu={'S': 'Save',
	#'L': 'Load',
	#'E': 'Exit'},
	#padding=(1,1),
	#position=(MAP_WINDOW_SIZE[0],0),
	#on_select=menu_item_selected)

#MAP = maputils.resize_map(MAP,(500,500,5))
#print MAP_SIZE
LIGHTS.append({'x': 40,'y': 30,'brightness': 20.0})
LIGHTS.append({'x': 20,'y': 25,'brightness': 20.0})

while RUNNING:
	get_input()
	handle_input()

	gfx.start_of_frame()
	
	if CYTHON_ENABLED:
		render_map.render_map(MAP)
	else:
		maps.render_map(MAP)
	
	maps.render_lights()
	
	LIGHTS[0]['x'] = CURSOR[0]
	LIGHTS[0]['y'] = CURSOR[1]
	#maps.render_shadows(MAP)
	#maps.soften_shadows(MAP)
	menu_align()
	gfx.draw_cursor(PLACING_TILE)
	gfx.draw_all_tiles()
	gfx.draw_bottom_ui_terraform()
	gfx.draw_selected_tile_in_item_window(TILES.index(PLACING_TILE))
	menus.draw_menus()
	gfx.draw_console()
	gfx.end_of_frame_terraform()
	gfx.end_of_frame()

maps.save_map(MAP)
