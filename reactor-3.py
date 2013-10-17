"""Reactor 3"""

import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('[%(asctime)s-%(levelname)s] %(message)s',datefmt='%H:%M:%S %m/%d/%y')
ch = logging.StreamHandler()
ch.setFormatter(console_formatter)
logger.addHandler(ch)

from globals import *
from inputs import *
from player import *

import libtcodpy as tcod
import render_fast_los
import render_map

import graphics as gfx
import traceback
import cProfile
import maputils
import worldgen
import mainmenu
import language
import profiles
import network
import drawing
import weapons
import effects
import numbers
import bullets
import dialog
import random
import numpy
import tiles
import menus
import logic
import items
import life
import time
import maps
import smp
import sys

CYTHON_ENABLED = True

def move_camera(pos,scroll=False):
	_orig_pos = CAMERA_POS[:]
	CAMERA_POS[0] = numbers.clip(pos[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0]-MAP_WINDOW_SIZE[0])
	CAMERA_POS[1] = numbers.clip(pos[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1]-MAP_WINDOW_SIZE[1])
	CAMERA_POS[2] = pos[2]
	
	if not _orig_pos == CAMERA_POS:
		gfx.refresh_window()
	elif SETTINGS['controlling'] and not alife.brain.get_flag(LIFE[SETTINGS['controlling']], 'redraw') == pos:
		gfx.refresh_window()
	
	if SETTINGS['controlling']:
		alife.brain.flag(LIFE[SETTINGS['controlling']], 'redraw', value=pos[:])

def draw_targeting():
	if LIFE[SETTINGS['controlling']] and LIFE[SETTINGS['controlling']]['targeting']:
		
		SELECTED_TILES[0] = []
		for pos in drawing.diag_line(LIFE[SETTINGS['controlling']]['pos'],LIFE[SETTINGS['controlling']]['targeting']):
			SELECTED_TILES[0].append((pos[0],pos[1],LIFE[SETTINGS['controlling']]['pos'][2]))

CURRENT_UPS = UPS

def main():
	global CURRENT_UPS
	
	get_input()
	handle_input()
	_played_moved = False

	while LIFE[SETTINGS['controlling']]['asleep']:
		logic.tick_all_objects(WORLD_INFO['map'])
		_played_moved = True
		
		if CURRENT_UPS:
			CURRENT_UPS-=1
		else:
			if life.is_target_of(LIFE[SETTINGS['controlling']]):
				CURRENT_UPS = 1
			else:
				CURRENT_UPS = 2 #ticks to run while actions are in queue before breaking
			
			gfx.refresh_window()
			break
	
	if not _played_moved:
		if CURRENT_UPS:
			CURRENT_UPS-=1
		else:
			CURRENT_UPS = 3
			logic.tick_all_objects(WORLD_INFO['map'])
			
	draw_targeting()
	move_camera(SETTINGS['camera_track'])
	
	if SELECTED_TILES[0]:
		gfx.refresh_window()
	
	if not SETTINGS['last_camera_pos'] == SETTINGS['camera_track']:
		_sight_distance = (alife.sight.get_vision(LIFE[SETTINGS['following']])/WORLD_INFO['chunk_size'])*(alife.sight.get_vision(LIFE[SETTINGS['following']])/2)
		
		LOS_BUFFER[0] = maps._render_los(WORLD_INFO['map'],
		                                 SETTINGS['camera_track'],
		                                 _sight_distance,
		                                 cython=True,
		                                 life=LIFE[SETTINGS['following']])
	SETTINGS['last_camera_pos'] = SETTINGS['camera_track'][:]
	
	maps.render_lights(WORLD_INFO['map'])
	
	if not SETTINGS['map_slices']:
		render_map.render_map(WORLD_INFO['map'])
	
	items.draw_items()
	bullets.draw_bullets()
	life.draw_life()
	
	if LIFE[SETTINGS['controlling']]['dead'] and not EVENTS:
		#TODO: Awful hack
		if not 'time_of_death' in LIFE[SETTINGS['controlling']]:
			LIFE[SETTINGS['controlling']]['time_of_death'] = WORLD_INFO['ticks']
		
		gfx.fade_to_white(FADE_TO_WHITE[0])
		_col = 255-int(round(FADE_TO_WHITE[0]))*2
		
		if _col<0:
			_col = 0
		#_col = 0
		
		_string = 'You die.'
		
		gfx.blit_string(MAP_WINDOW_SIZE[0]/2-(len(_string)/2),
			MAP_WINDOW_SIZE[1]/2,
			_string,
			console=MAP_WINDOW,
			fore_color=tcod.Color(_col, _col, _col),
			back_color=tcod.Color(255-_col,255-_col,255-_col),
			flicker=0)
		FADE_TO_WHITE[0] += 0.9
		
		if WORLD_INFO['ticks']-LIFE[SETTINGS['controlling']]['time_of_death']>=120:
			worldgen.save_world()
			worldgen.reset_world()
			SETTINGS['running'] = 1
			return False
	
	if SETTINGS['draw life info']:
		life.draw_life_info()
	
	menus.align_menus()
	menus.draw_menus()
	logic.draw_encounter()
	dialog.draw_dialog()
	
	if SETTINGS['draw message box']:
		gfx.draw_message_box()
	
	gfx.draw_status_line()
	gfx.draw_console()
	
	#TODO: Experimental map rendering, disabled for now
	if SETTINGS['map_slices']:
		maps.fast_draw_map()
	else:
		gfx.start_of_frame(draw_char_buffer=True)
		
	gfx.end_of_frame_reactor3()
	gfx.end_of_frame()
	
	if '--fps' in sys.argv:
		print tcod.sys_get_fps()

def loop():
	while SETTINGS['running']:
		if SETTINGS['running'] == 1:
			if not MENUS:
				mainmenu.switch_to_main_menu()
		
			get_input()
			handle_input()
			mainmenu.draw_main_menu()
		elif SETTINGS['running'] == 2:
			main()
		elif SETTINGS['running'] == 3:
			mainmenu.draw_intro()	

if __name__ == '__main__':
	#TODO: Replace with "module_sanity_check"
	#Optional Cython-compiled modules
	try:
		import render_map
		import render_los
		
		if render_map.VERSION == MAP_RENDER_VERSION:
			CYTHON_ENABLED = True
		else:
			logging.error('[Cython] render_map is out of date!')
			logging.error('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')
			sys.exit(1)
		
	except ImportError, e:
		CYTHON_ENABLED = False
		logging.warning('[Cython] ImportError with module: %s' % e)
		logging.warning('[Cython] Certain functions can run faster if compiled with Cython.')
		logging.warning('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')
	
	logging.info(WINDOW_TITLE)
	gfx.log(WINDOW_TITLE)
	
	if os.path.exists('git-version.txt'):
		with open('git-version.txt', 'r') as ver:
			logging.info('Build %s' % ver.readline().strip())
	
	logging.debug('Renderer: %s' % tcod.sys_get_renderer())
	
	tiles.create_all_tiles()
	language.load_strings()
	alife.rawparse.create_function_map()
	
	gfx.init_libtcod()
	#smp.init()

	SETTINGS['draw z-levels below'] = True
	SETTINGS['draw z-levels above'] = True
	
	life.initiate_life('human')
	life.initiate_life('dog')
	
	items.initiate_all_items()
	
	SETTINGS['running'] = 3
	
	if '--menu' in sys.argv:
		SETTINGS['running'] = 1
	elif '--quick' in sys.argv:
		for world in profiles.get_worlds():
			worldgen.load_world(world)
			break
		
		if LIFE:
			SETTINGS['running'] = 2
	
	if '--debug' in sys.argv:
		_debug_host = network.DebugHost()
		_debug_host.start()
		WORLD_INFO['debug'] = _debug_host
	
	if '--profile' in sys.argv:
		logging.info('Profiling. Exit when completed.')
		cProfile.run('loop()','profile.dat')
		sys.exit()
	
	try:
		loop()
	except Exception, e:
		traceback.print_exc(file=sys.stdout)
		SETTINGS['running'] = False
		
		if 'debug' in WORLD_INFO:
			WORLD_INFO['debug'].quit()
	
	if 'debug' in WORLD_INFO:
		WORLD_INFO['debug'].quit()
