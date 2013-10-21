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
import cProfile
import maputils
import numbers
import prefabs
import random
import items
import zones
import menus
import time
import maps
import sys
import smp

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
#smp.init()
create_all_tiles()
items.initiate_all_items()

LOAD_MAP = '1382326490.22.dat'

gfx.init_libtcod(terraform=True)

gfx.title('Loading...')
try:
	maps.load_map(LOAD_MAP)
except IOError:
	maps.create_map()
	maps.save_map()

console_set_keyboard_repeat(200, 30)
sys_set_fps(FPS_TERRAFORM)

SETTINGS['view'] = 'map'
PLACING_TILE = WALL_TILE

def handle_scrolling(cursor,camera,window_size,map_size,change):
	cursor[0] = numbers.clip(cursor[0]+change[0], 0, MAP_SIZE[0]-1)
	cursor[1] = numbers.clip(cursor[1]+change[1], 0, MAP_SIZE[1]-1)
	
	if change[0]>0:
		#if cursor[0]<map_size[0]-change[0]:
		#	cursor[0]+=change[0]
		
		if cursor[0]-camera[0]/2>window_size[0]/2 and camera[0]+window_size[0]<map_size[0]:
			camera[0]+=change[0]
		#if cursor[0]+camera[0]
	
	elif change[0]<0:
		#if cursor[0]>0:
		#	cursor[0]+=change[0]
		
		if cursor[0]-camera[0]<window_size[0]/2 and camera[0]>0:
			camera[0]+=change[0]
	
	if change[1]>0:
		#if cursor[1]<map_size[1]-change[1]:
		#	cursor[1]+=change[1]
		
		if cursor[1]-camera[1]/2>window_size[1]/2 and camera[1]+window_size[1]<map_size[1]:
			camera[1]+=change[1]
	
	elif change[1]<0:
		#if cursor[1]>0:
		#	cursor[1]+=change[1]
		
		if cursor[1]-camera[1]<window_size[1]/2 and camera[1]>0:
			camera[1]+=change[1]
	
	gfx.refresh_window()

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	if gfx.window_is_closed():
		SETTINGS['running'] = False
		
		return True
	
	elif INPUT['\x1b']:
		if not ACTIVE_MENU['menu'] == -1:
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
	
	elif menus.is_getting_input(ACTIVE_MENU['menu']):
		return

	elif INPUT['up']:
		if not ACTIVE_MENU['menu'] == -1:
			#MENUS[ACTIVE_MENU['menu']]['index'] = menus.find_item_before(MENUS[ACTIVE_MENU['menu']],index=MENUS[ACTIVE_MENU['menu']]['index'])
			menus.move_up(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['view'] == 'prefab':
			#TODO: Make this and everything in the `else` statement a function.
			handle_scrolling(PREFAB_CURSOR,PREFAB_CAMERA_POS,CURRENT_PREFAB['size'],MAP_WINDOW_SIZE,(0,-1))
		elif SETTINGS['view'] == 'chunk_map':
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(0, -WORLD_INFO['chunk_size']))
		else:
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(0, -1))

	elif INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.move_down(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['view'] == 'prefab':
			handle_scrolling(PREFAB_CURSOR,PREFAB_CAMERA_POS,PREFAB_WINDOW_SIZE,CURRENT_PREFAB['size'],	(0, 1))
		elif SETTINGS['view'] == 'chunk_map':
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(0, WORLD_INFO['chunk_size']))
		else:
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(0, 1))

	elif INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['view'] == 'prefab':
			handle_scrolling(PREFAB_CURSOR,PREFAB_CAMERA_POS,MAP_WINDOW_SIZE,CURRENT_PREFAB['size'],(1, 0))
		elif SETTINGS['view'] == 'chunk_map':
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(WORLD_INFO['chunk_size'], 0))
		else:
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(1, 0))

	elif INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['view'] == 'prefab':
			handle_scrolling(PREFAB_CURSOR,PREFAB_CAMERA_POS,MAP_WINDOW_SIZE,CURRENT_PREFAB['size'],(-1, 0))
		elif SETTINGS['view'] == 'chunk_map':
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(-WORLD_INFO['chunk_size'], 0))
		else:
			handle_scrolling(MAP_CURSOR,CAMERA_POS,MAP_WINDOW_SIZE,MAP_SIZE,(-1, 0))

	elif INPUT[' ']:
		if SETTINGS['view'] == 'prefab':
			CURRENT_PREFAB['map'][PREFAB_CURSOR[0]][PREFAB_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(PLACING_TILE)
		else:
			WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(PLACING_TILE)
	
	elif INPUT['m']:
		if SETTINGS['view'] == 'map':
			SETTINGS['view'] = 'chunk_map'
		else:
			SETTINGS['view'] = 'map'
		
		gfx.refresh_window()
	
	elif INPUT['n']:
		SUN_POS[2] -= 1
	
	elif INPUT['o']:
		if not ACTIVE_MENU['menu'] == -1:
			ACTIVE_MENU['menu'] = -1
			
			return True
		
		menus.activate_menu(0)
	
	elif INPUT['\r']:
		if ACTIVE_MENU['menu'] == -1:
			if SETTINGS['view'] == 'chunk_map':
				SETTINGS['view'] = 'map'
				gfx.refresh_window()
			return False
		
		menus.item_selected(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		ACTIVE_MENU['menu'] = -1
	
	elif INPUT['\t']:
		if SETTINGS['view'] == 'prefab':
			MENUS.pop(IN_PREFAB_EDITOR)
			ACTIVE_MENU['menu'] = -1
			IN_PREFAB_EDITOR = None
			create_options_menu()
		else:
			MENUS.pop()
			IN_PREFAB_EDITOR = prefabs.create_prefab_list()
			menus.activate_menu(IN_PREFAB_EDITOR)
	
	elif INPUT['q']:
		if SETTINGS['view'] == 'chunk_map':
			SETTINGS['view'] = 'map'
			gfx.refresh_window()
			return False
		
		_current_index = TILES.keys().index(PLACING_TILE['id'])-1
		
		if _current_index<0:
			_current_index = 0
		
		PLACING_TILE = TILES[TILES.keys()[_current_index]]
			
	elif INPUT['w']:
		_current_index = TILES.keys().index(PLACING_TILE['id'])+1
		
		if _current_index>=len(TILES):
			_current_index = len(TILES)-1
		
		PLACING_TILE = PLACING_TILE = TILES[TILES.keys()[_current_index]]
	
	elif INPUT['f']:
		#_matching = MAP[MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]].rpartition('_')[0]
		_matching = 'grass'
		
		#SELECTED_TILES[0] = maps.flood_select_by_tile(MAP,
		#	_matching,
		#	(MAP_CURSOR[0],MAP_CURSOR[1],CAMERA_POS[2]))

	elif INPUT['c']:
		WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(GRASS_TILES))

	elif INPUT['d']:
		if SETTINGS['view'] == 'prefab':
			CURRENT_PREFAB['map'][PREFAB_CURSOR[0]][PREFAB_CURSOR[1]][CAMERA_POS[2]] = None
		else:
			WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = None
	
	elif INPUT['a']:
		WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(SAND_TILES))
	
	elif INPUT['b']:
		WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(RED_BRICK_TILES))

	elif INPUT['g']:
		WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(CONCRETE_FLOOR_TILES))
	
	elif INPUT['h']:
		WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(WHITE_TILE_TILES))
	
	elif INPUT['s']:
		WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(DIRT_TILES))
	
	elif INPUT['z']:
		WORLD_INFO['map'][MAP_CURSOR[0]][MAP_CURSOR[1]][CAMERA_POS[2]] = \
				create_tile(random.choice(CONCRETE_TILES))

	elif INPUT['l']:
		SUN_BRIGHTNESS[0] += 4
	
	elif INPUT['k']:
		SUN_BRIGHTNESS[0] -= 4

	elif INPUT['1']:
		CAMERA_POS[2] = 1
		gfx.refresh_window()

	elif INPUT['2']:
		CAMERA_POS[2] = 2
		gfx.refresh_window()

	elif INPUT['3']:
		CAMERA_POS[2] = 3
		gfx.refresh_window()

	elif INPUT['4']:
		CAMERA_POS[2] = 4
		gfx.refresh_window()

	elif INPUT['5']:
		CAMERA_POS[2] = 5
		gfx.refresh_window()
	
	elif INPUT['6']:
		CAMERA_POS[2] = 6
		gfx.refresh_window()
	
	elif INPUT['7']:
		CAMERA_POS[2] = 7
		gfx.refresh_window()
	
	elif INPUT['8']:
		CAMERA_POS[2] = 8
		gfx.refresh_window()
	
	elif INPUT['9']:
		CAMERA_POS[2] = 9
		gfx.refresh_window()
	
	elif INPUT['0']:
		CAMERA_POS[2] = 0
		gfx.refresh_window()

def menu_item_selected(entry):
	global RUNNING
	value = entry['values'][entry['value']]
	
	if value == 'Save':
		console_set_default_foreground(0, white)
		console_print(0, 0, 0, 'Saving...')
		console_flush()
		
		maps.save_map(LOAD_MAP)
	elif value == 'Save Prefab':
		prefabs.save(CURRENT_PREFAB)
	elif value == 'Compile':
		_stime = time.time()
		
		maps.update_chunk_map()
		maps.smooth_chunk_map()
		maps.generate_reference_maps()
		zones.create_zone_map()
		zones.connect_ramps()
		
		logging.debug('Map compile took: %s' % (time.time()-_stime))
	elif value == 'Generate chunk map':
		maps.update_chunk_map()
		maps.smooth_chunk_map()
		maps.generate_reference_maps()
		
	elif value == 'Exit':
		SETTINGS['running'] = False

def menu_item_changed(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Blit z-level below':
		if value == 'On':
			SETTINGS['draw z-levels below'] = True
		elif value == 'Off':
			SETTINGS['draw z-levels below'] = False
		
		gfx.refresh_window()
	
	elif key == 'Blit z-level above':
		if value == 'On':
			SETTINGS['draw z-levels above'] = True
		elif value == 'Off':
			SETTINGS['draw z-levels above'] = False
		
		gfx.refresh_window()
	
	elif key == 'Draw lights':
		if value == 'On':
			SETTINGS['draw lights'] = True
		elif value == 'Off':
			maps.reset_lights()
			SETTINGS['draw lights'] = False
		
		gfx.refresh_window()

def menu_align():
	for menu in MENUS:
		if not MENUS.index(menu):
			continue
		
		_prev_menu = MENUS[MENUS.index(menu)-1]
		_size = _prev_menu['settings']['position'][1]+_prev_menu['settings']['size'][1]
		
		menu['settings']['position'][1] = _size

def create_options_menu():
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
	
	_menu_items.append(menus.create_item('title','Prefab',None,enabled=False))
	_menu_items.append(menus.create_item('input','Name',''))
	_menu_items.append(menus.create_item('list','S','Save Prefab'))
	_menu_items.append(menus.create_item('spacer','=',None,enabled=False))
	
	_menu_items.append(menus.create_item('title','General',None,enabled=False))
	_menu_items.append(menus.create_item('list','S','Save'))
	_menu_items.append(menus.create_item('list','C','Compile'))
	_menu_items.append(menus.create_item('list','CH','Generate chunk map'))
	_menu_items.append(menus.create_item('list','L','Load'))
	_menu_items.append(menus.create_item('list','E','Exit'))
	
	menus.create_menu(title='Options',
		menu=_menu_items,
		padding=(1,1),
		position=(MAP_WINDOW_SIZE[0],0),
		on_select=menu_item_selected,
		on_change=menu_item_changed)
	
	menu_align()

prefabs.cache_all_prefabs()
CURRENT_PREFAB = prefabs.create_new_prefab((5, 5, 5))
create_options_menu()

def main():
	while SETTINGS['running']:
		get_input()
		handle_input()
		
		if SETTINGS['view'] == 'prefab':
			#prefabs.draw_prefab_editor()#(CURRENT_PREFAB)
			gfx.draw_cursor(PREFAB_CURSOR,
				PREFAB_CAMERA_POS,
				PLACING_TILE,
				char_buffer=PREFAB_CHAR_BUFFER,
				rgb_fore_buffer=PREFAB_RGB_FORE_BUFFER,
				rgb_back_buffer=PREFAB_RGB_BACK_BUFFER)
		
		elif SETTINGS['view'] == 'chunk_map':
			gfx.draw_chunk_map()
			
		else:
			LOS_BUFFER[0] = numpy.ones((MAP_WINDOW_SIZE[1], MAP_WINDOW_SIZE[0]))

			if CYTHON_ENABLED:
				render_map.render_map(WORLD_INFO['map'])
			else:
				maps.render_map(WORLD_INFO['map'])
			
			#TODO: Cython-ify
			maps.render_x_cutout(WORLD_INFO['map'],MAP_CURSOR[0],MAP_CURSOR[1])
			maps.render_y_cutout(WORLD_INFO['map'],MAP_CURSOR[0],MAP_CURSOR[1])
			
			#items.draw_items()
			gfx.draw_all_tiles()
			gfx.draw_bottom_ui_terraform()
			gfx.draw_console()
			gfx.draw_cursor(MAP_CURSOR,CAMERA_POS,PLACING_TILE)
		
		menus.draw_menus()
		
		gfx.draw_selected_tile_in_item_window(TILES.keys().index(PLACING_TILE['id']))
		gfx.start_of_frame(draw_char_buffer=(menus.get_menu_by_name('Prefabs')==-1))
		
		if menus.get_menu_by_name('Prefabs')==-1:
			gfx.start_of_frame_terraform()
		
		gfx.end_of_frame_terraform(draw_cutouts=(not SETTINGS['view'] == 'prefab'))
		gfx.end_of_frame(draw_map=(menus.get_menu_by_name('Prefabs')==-1))

if '--profile' in sys.argv:
	logging.info('Profiling. Exit when completed.')
	cProfile.run('main()','profile.dat')
else:
	try:
		main()
	except Exception, e:
		logging.exception('Crashed: %s' % e)

#TODO: write this into the utility
#MAP = maputils.resize_map(MAP,(MAP_SIZE[0],MAP_SIZE[1],MAP_SIZE[2]+5))

maps.save_map(LOAD_MAP)
