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
	
	effect['top_left'] = _top_left
	
	#print _top_left
	
	target_los = render_los.render_los(source_map,where,top_left=_top_left,no_edge=False)
	target_los = numpy.multiply(target_los,50)
	
	effect['height_map'] = target_los
	
	register_effect(effect,simulate_gas)

def simulate_gas(effect):
	effect['height_map'] = numpy.multiply(effect['height_map'],0.99)
	
	return True

def tick_effects():
	#global EFFECTS
	_t = time.time()
	for effect in EFFECTS[:]:		
		if not effect['callback'](effect):
			EFFECTS.remove(effect)
	
	print time.time()-_t
