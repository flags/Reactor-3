from globals import *

import alife as alfe
import libtcodpy as tcod

import encounters
import menus
import items
import life

def tick_all_objects(source_map):
	if WORLD_INFO['in_combat'] and SETTINGS['controlling']['actions']:
		WORLD_INFO['pause_ticks'] = 0
	
	if WORLD_INFO['pause_ticks']:
		WORLD_INFO['pause_ticks'] -= 1
		return False
	
	if menus.get_menu_by_name('Select Limb')>-1 or menus.get_menu_by_name('Select Target')>-1:
		return False
	
	if SETTINGS['controlling']:
		if SETTINGS['controlling']['targeting'] and SETTINGS['controlling']['shoot_timer']:
			SETTINGS['controlling']['shoot_timer']-=1
			return False
		
		if SETTINGS['controlling']['contexts'] and SETTINGS['controlling']['shoot_timer']:
			#TODO: Just disable this...
			SETTINGS['controlling']['shoot_timer'] = 0
			return False
		
		if SETTINGS['controlling']['encounters']:
			return False
		
		#if menus.get_menu_by_name('Aim at...') > -1:
		#	return False
		if SETTINGS['controlling']['targeting']:
			return False
		
		if life.has_dialog(SETTINGS['controlling']):
			return False
	
		_in_combat = False
		for alife in [LIFE[i] for i in LIFE]:
			if SETTINGS['controlling']['id'] == alife['id']:
				continue
			
			if alife['asleep'] or alife['dead']:
				continue
			
			_x,_y = alife['pos'][:2]
			
			if alife['pos'][0]>CAMERA_POS[0]:
				_x = alife['pos'][0]-CAMERA_POS[0]
			
			if alife['pos'][1]>CAMERA_POS[1]:
				_y = alife['pos'][1]-CAMERA_POS[1]
			
			if _x>=40:
				continue
			
			if _y>=40:
				continue
			
			if not LOS_BUFFER[0][_y, _x]:
				continue
			
			_targets = alfe.brain.retrieve_from_memory(alife, 'combat_targets')
			if _targets and SETTINGS['controlling']['id'] in [l['who']['life']['id'] for l in _targets]:
				_in_combat = True
				
				if not WORLD_INFO['pause_ticks']:
					if tcod.sys_get_fps()<=LOW_FPS:
						WORLD_INFO['pause_ticks'] = 1
					else:
						WORLD_INFO['pause_ticks'] = 2
			
			WORLD_INFO['in_combat'] = _in_combat
	
	items.tick_all_items(source_map)
	life.tick_all_life(source_map)
	
	return True

def tick_world():
	WORLD_INFO['ticks'] += 1

def draw_encounter():
	if not SETTINGS['controlling']['encounters']:
		return False
	
	encounters.draw_encounter(SETTINGS['controlling'],
		SETTINGS['controlling']['encounters'][0])

def matches(dict1, dict2):
	_break = False
	for key in dict2:
		if not key in dict1 or not dict1[key] == dict2[key]:
			return False
	
	return True