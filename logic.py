from globals import *

import encounters
import items
import life

def tick_all_objects(source_map):
	if SETTINGS['controlling']:
		if SETTINGS['controlling']['targeting'] and SETTINGS['controlling']['shoot_timer']:
			SETTINGS['controlling']['shoot_timer']-=1
			return False
		
		if SETTINGS['controlling']['contexts'] and SETTINGS['controlling']['shoot_timer']:
			SETTINGS['controlling']['shoot_timer'] -= 1
			return False
		
		if SETTINGS['controlling']['encounters']:
			return False
	
	items.tick_all_items(source_map)
	life.tick_all_life(source_map)
	
	return True

def tick_world():
	WORLD_INFO['ticks'] += 1

def draw_encounter():
	if not SETTINGS['controlling']['encounters']:
		return False
	
	encounters.draw_encounter(SETTINGS['controlling'],
		SETTINGS['controlling']['encounters'][SETTINGS['controlling']['encounters'].keys()[0]])
