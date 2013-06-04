from globals import *

import libtcodpy as tcod
import graphics as gfx

import render_los
import logging
import numbers
import random
import numpy
import time
import maps
import sys

def register_effect(effect, callback):
	effect['callback'] = callback
	
	EFFECTS.append(effect)
	
	logging.debug('Effect registered: %s' % effect['what'])

def has_splatter(position, what=None):
	#TODO: Make this into a dict so we can convert the position to a string and search that
	for splat in SPLATTERS:
		if splat['pos'] == position:
			if what and not what == splat['what']:
				continue
			
			return splat

def create_splatter(what, position, velocity=0):
	_splatter = has_splatter(tuple(position),what=what)
	
	if not _splatter:
		_splatter = {'pos': list(position[:]),'what': what,'color': tcod.Color(0,0,0),'coef': numbers.clip(random.random(), 0, 0.3)}
		_splatter['pos'][0] += random.randint(-velocity,velocity)
		_splatter['pos'][1] += random.randint(-velocity,velocity)
	
		if what == 'blood':
			_splatter['color'].r = 150
	else:
		_splatter['coef'] += 0.3
		_splatter['coef'] = numbers.clip(_splatter['coef'],0,1)
		
		return True
	
	_splatter['pos'] = tuple(_splatter['pos'])
	SPLATTERS.append(_splatter)

def create_gas(where, what, amount, source_map):
	effect = {'what': what, 'where': tuple(where),'amount': amount,'map': source_map,'height_map': 'Reset'}
	
	_x = numbers.clip(where[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0])
	_y = numbers.clip(where[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1])
	_top_left = (_x,_y,where[2])
	
	effect['top_left'] = _top_left
	
	target_los = render_los.render_los(source_map,where,top_left=_top_left,no_edge=False)
	target_los = numpy.multiply(target_los,50)
	
	effect['height_map'] = target_los
	
	register_effect(effect,simulate_gas)

def simulate_gas(effect):
	effect['height_map'] = numpy.multiply(effect['height_map'],0.99)
	
	return True

def draw_splatter(position, render_at):
	_has_splatter = has_splatter(position)
	
	if not _has_splatter:
		return False
	
	gfx.tint_tile(render_at[0],render_at[1],_has_splatter['color'],_has_splatter['coef'])

def tick_effects():
	#global EFFECTS
	_t = time.time()
	for effect in EFFECTS[:]:		
		if not effect['callback'](effect):
			EFFECTS.remove(effect)
	
	print time.time()-_t
