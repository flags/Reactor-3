from globals import *
import graphics as gfx
import render_los
import logging
import numbers
import numpy
import time
import maps
import sys

def register_effect(effect,callback):
	effect['callback'] = callback
	
	EFFECTS.append(effect)
	
	logging.debug('Effect registered: %s' % effect['what'])

def create_splatter(life,what):
	pass
	#gfx.message('%s splatters on the ground.')

def create_gas(where,what,amount,source_map):
	effect = {'what': what, 'where': tuple(where),'amount': amount,'map': source_map,'height_map': 'Reset'}
	
	_x = numbers.clip(where[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0])
	_y = numbers.clip(where[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1])
	_top_left = (_x,_y,where[2])
	target_los = render_los.render_los(source_map,where,top_left=_top_left,no_edge=False)
	
	print numpy.multiply(target_los,30)
	
	effect['height_map'] = target_los
	
	register_effect(effect,simulate_gas)

def simulate_gas(effect):
	X_SIZE = 40
	Y_SIZE = 40
	
	#print 'Simulating'
	
	if not effect['height_map'] == 'Reset':
		MAP = effect['height_map']
	else:
		print 'New map?'
		MAP = maps.get_collision_map(effect['map'],(0,0,2),(40,40),mark=-1)
		MAP[13,25] = 7
	
	NEXT_MAP = MAP.copy()
	
	for MOD_Y in range(X_SIZE-1):
		for MOD_X in range(Y_SIZE-1):
			if MAP[MOD_Y,MOD_X] == -1:
				continue
			
			LARGEST_SCORE = MAP[MOD_Y,MOD_X]+.90
			
			for X_OFFSET in range(-1,2):
				for Y_OFFSET in range(-1,2):
					x = MOD_X+X_OFFSET
					y = MOD_Y+Y_OFFSET
					
					if 0>x or 0>y or x>=X_SIZE-1 or y>=Y_SIZE-1 or MAP[y,x]<=-1:
						continue
					
					if MAP[y,x] > LARGEST_SCORE:
						LARGEST_SCORE = MAP[y,x]
					
			NEXT_MAP[MOD_Y,MOD_X] = LARGEST_SCORE-(0.95)
			
			if NEXT_MAP[MOD_Y,MOD_X]<0:
				NEXT_MAP[MOD_Y,MOD_X] = 0
	
	#draw_map(NEXT_MAP)
	
	if numpy.array_equal(effect['height_map'],NEXT_MAP):
		effect['pause'] = True
		return False
	
	effect['height_map'] = NEXT_MAP.copy()
	#print NEXT_MAP
	
	return True

def tick_effects():
	#global EFFECTS
	_t = time.time()
	for effect in EFFECTS[:]:		
		if not effect['callback'](effect):
			EFFECTS.remove(effect)
	
	print time.time()-_t
