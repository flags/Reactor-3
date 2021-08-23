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
import missions
import threads
import network
import drawing
import weapons
import effects
import bad_numbers
import dialog
import random
import numpy
import tiles
import menus
import logic
import locks
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
	
	if SETTINGS['controlling'] and SETTINGS['following'] == SETTINGS['controlling'] and locks.is_locked('camera_free'):
		_life = LIFE[SETTINGS['controlling']]
		_top_left = MAP_SIZE[:]
		_bot_right = [0, 0, 0]
		_seen = False
		
		for life_id in LIFE[SETTINGS['controlling']]['seen']:
			if LIFE[life_id]['dead']:
				continue
			
			if brain.knows_alife_by_id(LIFE[SETTINGS['controlling']], life_id)['alignment'] in ['trust', 'feign_trust']:
				continue
			
			_seen = True
			
			if LIFE[life_id]['pos'][0] < _top_left[0]:
				_top_left[0] = LIFE[life_id]['pos'][0]
			
			if LIFE[life_id]['pos'][1] < _top_left[1]:
				_top_left[1] = LIFE[life_id]['pos'][1]
			
			if LIFE[life_id]['pos'][0] > _bot_right[0]:
				_bot_right[0] = LIFE[life_id]['pos'][0]
			
			if LIFE[life_id]['pos'][1] > _bot_right[1]:
				_bot_right[1] = LIFE[life_id]['pos'][1]
			
			_target_pos = bad_numbers.lerp_velocity(_top_left, _bot_right, 0.5)
			pos = bad_numbers.lerp_velocity(pos, _target_pos, .35)[:2]
			pos.append(2)
			
			brain.flag(_life, 'camera_lean', value=_target_pos[:])
			brain.flag(_life, 'camera_lean_time', value=WORLD_INFO['ticks'])
			
			_future_time = brain.get_flag(_life, 'camera_lean_time_future')
			if not _future_time or WORLD_INFO['ticks']>_future_time:
				brain.flag(_life, 'camera_lean_time_future', value=WORLD_INFO['ticks']+30)
		
		if brain.get_flag(_life, 'camera_lean'):
			if _seen:
				_st = WORLD_INFO['ticks']-(brain.get_flag(_life, 'camera_lean_time_future')-30)
				_et = brain.get_flag(_life, 'camera_lean_time_future')-(brain.get_flag(_life, 'camera_lean_time_future')-30)
				_lerp = 1-bad_numbers.clip(_st/float(_et), 0, 1.0)
				
				pos = bad_numbers.lerp_velocity(pos, brain.get_flag(_life, 'camera_lean'), _lerp)[:2]
				pos.append(2)
			else:
				if WORLD_INFO['ticks']-brain.get_flag(_life, 'camera_lean_time')<=20:
					_lerp = .45-bad_numbers.clip((WORLD_INFO['ticks']-brain.get_flag(_life, 'camera_lean_time'))/30.0, 0, .45)
					pos = bad_numbers.lerp_velocity(pos, brain.get_flag(_life, 'camera_lean'), _lerp)[:2]
					pos.append(2)
				else:
					brain.unflag(_life, 'camera_lean')
					brain.unflag(_life, 'camera_lean_time')
	
	CAMERA_POS[0] = int(round(bad_numbers.clip(pos[0]-(MAP_WINDOW_SIZE[0]//2), 0, MAP_SIZE[0]-MAP_WINDOW_SIZE[0])))
	CAMERA_POS[1] = int(round(bad_numbers.clip(pos[1]-(MAP_WINDOW_SIZE[1]//2), 0, MAP_SIZE[1]-MAP_WINDOW_SIZE[1])))
	CAMERA_POS[2] = int(round(pos[2]))
	
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
	_player = LIFE[SETTINGS['controlling']]
	
	maps.reset_lights()
	FADE_TO_WHITE[0] += .5
	
	_time_since_death = FADE_TO_WHITE[0]
	_time_alive = round(bad_numbers.clip((_player['time_of_death']-_player['created'])/float(WORLD_INFO['length_of_day']), 0.1, 9999), 2)
	_string = 'You die.'
	_sub_string = _player['cause_of_death']
	_col = int(round(255*bad_numbers.clip((_time_since_death/100.0)-random.uniform(0, 0.15), 0, 1)))
	
	
	if _time_alive == 1:
		_sub_sub_string = 'Lived 1 day'
	else:
		if _time_alive < 1:
			_sub_sub_string = 'Lived less than a day'
		else:
			_sub_sub_string = 'Lived %0.1f days' % (_time_alive)
	
	gfx.fade_to_black(1)	
	
	gfx.blit_string((MAP_WINDOW_SIZE[0]//2)-len(_string)//2,
	                MAP_WINDOW_SIZE[1]//2,
	                _string,
	                'map',
	                fore_color=tcod.Color(_col, 0, 0),
	                back_color=tcod.Color(0, 0, 0))
	
	gfx.blit_string((MAP_WINDOW_SIZE[0]//2)-len(_sub_string)//2,
	                (MAP_WINDOW_SIZE[1]//2)+2,
	                _sub_string,
	                'map',
	                fore_color=tcod.Color(int(round(_col*.75)), int(round(_col*.75)), int(round(_col*.75))),
	                back_color=tcod.Color(0, 0, 0))
	
	gfx.blit_string((MAP_WINDOW_SIZE[0]//2)-len(_sub_sub_string)//2,
	                (MAP_WINDOW_SIZE[1]//2)+4,
	                _sub_sub_string,
	                'map',
	                fore_color=tcod.Color(int(round(_col*.75)), int(round(_col*.75)), int(round(_col*.75))),
	                back_color=tcod.Color(0, 0, 0))
	
	if _time_since_death>=350:
		worldgen.save_world()
		worldgen.reset_world()

		gfx.clear_scene()
		
		SETTINGS['running'] = 1
		return False
	
	return True

def main():
	_player_moved = False
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

			gfx.title(LIFE[SETTINGS['controlling']]['asleep_reason'])
			logic.tick_all_objects(ignore_tickrate=True, ignore_pause=True)
			
			if LIFE[SETTINGS['controlling']]['dead']:
				break
	else:
		_player_moved = True
	
	if _refresh_map:
		gfx.refresh_view('map')
	
	if not _player_moved:
		if logic.tick_all_objects(ignore_tickrate=True):
			_player_moved = True
	
	draw_targeting()
	move_camera(SETTINGS['camera_track'])
	
	#TODO: Deselect so we can get rid of this call
	if SELECTED_TILES[0]:
		gfx.refresh_view('map')
	
	if not SETTINGS['last_camera_pos'] == SETTINGS['camera_track'][:]:
		if EVENTS or MENUS:
			_visible_chunks = sight.scan_surroundings(LIFE[SETTINGS['following']], judge=False, get_chunks=True)
			alife.brain.flag(LIFE[SETTINGS['following']], 'visible_chunks', value=_visible_chunks)
	
			_cam_x = bad_numbers.clip(LIFE[SETTINGS['following']]['pos'][0]-MAP_WINDOW_SIZE[0]//2, 0, MAP_SIZE[0]-MAP_WINDOW_SIZE[0]//2)
			_cam_y = bad_numbers.clip(LIFE[SETTINGS['following']]['pos'][1]-MAP_WINDOW_SIZE[1]//2, 0, MAP_SIZE[1]-MAP_WINDOW_SIZE[1]//2)
			
		else:
			_visible_chunks = sight.scan_surroundings(LIFE[SETTINGS['controlling']], judge=False, get_chunks=True)
			alife.brain.flag(LIFE[SETTINGS['controlling']], 'visible_chunks', value=_visible_chunks)
			
		SETTINGS['last_camera_pos'] = SETTINGS['camera_track'][:]
	
	_cam_x = bad_numbers.clip(LIFE[SETTINGS['controlling']]['pos'][0]-MAP_WINDOW_SIZE[0]//2, 0, MAP_SIZE[0]-MAP_WINDOW_SIZE[0]//2)
	_cam_y = bad_numbers.clip(LIFE[SETTINGS['controlling']]['pos'][1]-MAP_WINDOW_SIZE[1]//2, 0, MAP_SIZE[1]-MAP_WINDOW_SIZE[1]//2)
	
	maps.render_lights()
	
	if '--worldmap' in sys.argv:
		render_map.render_map(WORLD_INFO['map'], force_camera_pos=(_cam_x, _cam_y, 2))
	else:
		render_map.render_map(WORLD_INFO['map'], los=LIFE[SETTINGS['controlling']]['fov'], force_camera_pos=(_cam_x, _cam_y, 2))
	
	items.draw_items()
	life.draw_life()
	
	if LIFE[SETTINGS['controlling']]['dead'] and not EVENTS:
		if not death():
			return False
	
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
		print(tcod.sys_get_fps())
	
	if (SETTINGS['recording'] and _player_moved and not EVENTS and not MENUS) or '--worldmap' in sys.argv:
		gfx.screenshot()
		
		if '--worldmap' in sys.argv:
			SETTINGS['running'] = False

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
		
	except ImportError as e:
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
	language.load_dialog()
	missions.load_all_missions()
	alife.rawparse.create_function_map()
	locks.create_lock('camera_free', locked=True)
	
	gfx.init_libtcod()
	threads.init()
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
	except KeyboardInterrupt:
		SETTINGS['running'] = False
		traceback.print_exc()
	except Exception as e:
		traceback.print_exc()
		SETTINGS['running'] = False
		
		if 'debug' in WORLD_INFO:
			WORLD_INFO['debug'].quit()
	
	if 'debug' in WORLD_INFO:
		WORLD_INFO['debug'].quit()
