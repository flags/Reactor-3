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
import fov
import smp
import sys

CYTHON_ENABLED = True

def move_camera(pos, scroll=False):
	_orig_pos = CAMERA_POS[:]
	CAMERA_POS[0] = numbers.clip(pos[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0]-MAP_WINDOW_SIZE[0])
	CAMERA_POS[1] = numbers.clip(pos[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1]-MAP_WINDOW_SIZE[1])
	CAMERA_POS[2] = pos[2]
	
	if not _orig_pos == CAMERA_POS:
		gfx.refresh_view('map')
	elif SETTINGS['controlling'] and not alife.brain.get_flag(LIFE[SETTINGS['controlling']], 'redraw') == pos:
		gfx.refresh_view('map')
	
	if SETTINGS['controlling']:
		alife.brain.flag(LIFE[SETTINGS['controlling']], 'redraw', value=pos[:])

def draw_targeting():
	if SETTINGS['following'] and not SETTINGS['controlling'] == SETTINGS['following'] and LIFE[SETTINGS['following']]['path']:
		SELECTED_TILES[0] = [(p[0], p[1], 2) for p in LIFE[SETTINGS['following']]['path']]
	
	if LIFE[SETTINGS['controlling']] and LIFE[SETTINGS['controlling']]['targeting']:
		
		SELECTED_TILES[0] = []
		for pos in drawing.diag_line(LIFE[SETTINGS['controlling']]['pos'],LIFE[SETTINGS['controlling']]['targeting']):
			SELECTED_TILES[0].append((pos[0],pos[1],LIFE[SETTINGS['controlling']]['pos'][2]))

def death():
	#TODO: Awful hack
	if not 'time_of_death' in LIFE[SETTINGS['controlling']]:
		LIFE[SETTINGS['controlling']]['time_of_death'] = WORLD_INFO['ticks']
	
	gfx.fade_to_white(FADE_TO_WHITE[0])
	
	_string = 'You die.'
	_time_since_death = WORLD_INFO['ticks']-LIFE[SETTINGS['controlling']]['time_of_death']
	_col = int(round(255*numbers.clip((_time_since_death/100.0)-random.uniform(0, 0.15), 0, 1)))
	
	for i in range(len(_string)):
		_c = _string[i]
		gfx.lighten_tile(MAP_WINDOW_SIZE[0]/2-(len(_string)/2)+i, MAP_WINDOW_SIZE[1]/2, _col)
		gfx.blit_char_to_view(MAP_WINDOW_SIZE[0]/2-(len(_string)/2)+i,
	                   MAP_WINDOW_SIZE[1]/2,
	                   _c,
	                   (tcod.Color(_col, 0, 0),
	                    tcod.Color(255-_col, 255-_col, 255-_col)),
	                   'map')
	
	if _time_since_death>=25:
		_fade = numbers.clip((_time_since_death)/100.0, 0, 1)
		_summary = 'Lived %s days.' % ((LIFE[SETTINGS['controlling']]['time_of_death']-LIFE[SETTINGS['controlling']]['created'])/float(WORLD_INFO['length_of_day']))
		gfx.blit_string((MAP_WINDOW_SIZE[0]/2)-len(_summary)/2, (MAP_WINDOW_SIZE[1]/2)+2, _summary, fore_color=tcod.crimson, view_name='overlay')
		gfx.fade_view('overlay', _fade, 0)
	
	FADE_TO_WHITE[0] += 1.2
	
	if _time_since_death>=120:
		worldgen.save_world()
		worldgen.reset_world()

		gfx.clear_scene()
		
		SETTINGS['running'] = 1
		return False

def main():
	_played_moved = False
	_refresh_map = False
	
	get_input()
	handle_input()
	
	if not LIFE[SETTINGS['controlling']]['dead']:
		if LIFE[SETTINGS['controlling']]['asleep']:
			gfx.fade_to_black(255)
			gfx.start_of_frame()
			gfx.end_of_frame()
	
		while LIFE[SETTINGS['controlling']]['asleep']:
			_played_moved = True
			_refresh_map = True

			gfx.title('Sleeping')
			logic.tick_all_objects(ignore_tickrate=True, ignore_pause=True)
			
			print LIFE[SETTINGS['controlling']]['asleep'], LIFE[SETTINGS['controlling']]['dead']
			if LIFE[SETTINGS['controlling']]['dead']:
				break
	
	if _refresh_map:
		gfx.refresh_view('map')
	
	if not _played_moved:
		logic.tick_all_objects(ignore_tickrate=True)
	
	draw_targeting()
	move_camera(SETTINGS['camera_track'])
	
	#TODO: Deselect so we can get rid of this call
	if SELECTED_TILES[0]:
		gfx.refresh_view('map')
	
	if not SETTINGS['last_camera_pos'] == SETTINGS['camera_track'][:]:
		if EVENTS or MENUS:
			_visible_chunks = sight.scan_surroundings(LIFE[SETTINGS['following']], judge=False, get_chunks=True)
			alife.brain.flag(LIFE[SETTINGS['following']], 'visible_chunks', value=_visible_chunks)
	
			_cam_x = numbers.clip(LIFE[SETTINGS['following']]['pos'][0]-MAP_WINDOW_SIZE[0]/2, 0, MAP_SIZE[0]-MAP_WINDOW_SIZE[0]/2)
			_cam_y = numbers.clip(LIFE[SETTINGS['following']]['pos'][1]-MAP_WINDOW_SIZE[1]/2, 0, MAP_SIZE[1]-MAP_WINDOW_SIZE[1]/2)
			
		else:
			_visible_chunks = sight.scan_surroundings(LIFE[SETTINGS['controlling']], judge=False, get_chunks=True)
			alife.brain.flag(LIFE[SETTINGS['controlling']], 'visible_chunks', value=_visible_chunks)
			
		SETTINGS['last_camera_pos'] = SETTINGS['camera_track'][:]
	
	_cam_x = numbers.clip(LIFE[SETTINGS['controlling']]['pos'][0]-MAP_WINDOW_SIZE[0]/2, 0, MAP_SIZE[0]-MAP_WINDOW_SIZE[0]/2)
	_cam_y = numbers.clip(LIFE[SETTINGS['controlling']]['pos'][1]-MAP_WINDOW_SIZE[1]/2, 0, MAP_SIZE[1]-MAP_WINDOW_SIZE[1]/2)
	
	maps.render_lights()
	render_map.render_map(WORLD_INFO['map'], los=LIFE[SETTINGS['controlling']]['fov'], force_camera_pos=(_cam_x, _cam_y, 2))
	items.draw_items()
	life.draw_life()
	
	if LIFE[SETTINGS['controlling']]['dead'] and not EVENTS:
		death()
	
	if SETTINGS['draw life info'] and SETTINGS['following']:
		life.draw_life_info()
	
	gfx.draw_message_box()
	
	menus.align_menus()
	menus.draw_menus()
	
	gfx.draw_status_line()
	gfx.draw_console()
	gfx.start_of_frame()
	gfx.end_of_frame()
	
	if '--fps' in sys.argv:
		print tcod.sys_get_fps()
	
	if SETTINGS['recording'] and logic.can_tick():
		#	if 10+SETTINGS['recording fps temp']:
		#		SETTINGS['recording fps temp'] -= 1
		#	else:
		#		WORLD_INFO['d'] = WORLD_INFO['ticks']
			gfx.screenshot()
	#		SETTINGS['recording fps temp'] = SETTINGS['recording fps']

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
	
	worldgen.cleanup()

if __name__ == '__main__':
	profiles.version_check()
	
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
	life.initiate_life('night_terror')
	
	items.initiate_all_items()
	
	SETTINGS['running'] = 3
	
	if '--menu' in sys.argv:
		SETTINGS['running'] = 1
	elif '--quick' in sys.argv:
		for world in profiles.get_worlds():
			worldgen.load_world(world)
			break
		
		if SETTINGS['controlling']:
			SETTINGS['running'] = 2
			gfx.prepare_map_views()
		else:
			logging.debug('No active player found. Going back to menu.')
			SETTINGS['running'] = 1
	
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
