from globals import *

import encounters
import alife as alfe
import items
import life

def tick_all_objects(source_map):
	if WORLD_INFO['in_combat'] and SETTINGS['controlling']['actions']:
		WORLD_INFO['pause_ticks'] = 0
	
	if WORLD_INFO['pause_ticks']:
		WORLD_INFO['pause_ticks'] -= 1
		return False
	
	if SETTINGS['controlling']:
		if SETTINGS['controlling']['targeting'] and SETTINGS['controlling']['shoot_timer']:
			SETTINGS['controlling']['shoot_timer']-=1
			return False
		
		if SETTINGS['controlling']['contexts'] and SETTINGS['controlling']['shoot_timer']:
			SETTINGS['controlling']['shoot_timer'] -= 1
			return False
		
		if SETTINGS['controlling']['encounters']:
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
					WORLD_INFO['pause_ticks'] = 15
			
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
