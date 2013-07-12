from globals import *

import libtcodpy as tcod
import graphics as gfx

import render_los
import numbers
import items
import maps

import logging
import random
import numpy
import time
import sys

def create_effect_map():
	for x in range(0, MAP_SIZE[0]):
		_y = []
		
		for y in range(0, MAP_SIZE[1]):
			_y.append([])
		
		EFFECT_MAP.append(_y)
	
	logging.debug('Effect map created.')

def register_effect(effect):
	effect['id'] = WORLD_INFO['effectid']
	EFFECTS[effect['id']] = effect
	EFFECT_MAP[effect['pos'][0]][effect['pos'][1]].append(effect['id'])
	
	WORLD_INFO['effectid'] += 1

def unregister_effect(effect):
	EFFECT_MAP[effect['pos'][0]][effect['pos'][1]].remove(effect['id'])
	del EFFECTS[effect['id']]

def draw_fire(pos, fire):
	_intensity = fire['intensity']/float(8)
	_rand_intensity = numbers.clip(_intensity-random.uniform(0, .2), 0, 1)
	
	gfx.tint_tile(pos[0], pos[1], fire['color'], _rand_intensity)

def calculate_fire(fire):
	_neighbor_intensity = 0
	
	for x in range(-1, 2):
		_x = fire['pos'][0]+x
		
		if -1>_x>MAP_SIZE[0]:
			continue
		
		for y in range(-1, 2):
			if not x and not y:
				continue
			
			_y = fire['pos'][1]+y
			
			if -1>_y>MAP_SIZE[1]:
				continue
			
			for effect in [EFFECTS[eid] for eid in EFFECT_MAP[_x][_y] if EFFECTS[eid]['type'] == 'fire']:
				_neighbor_intensity += effect['intensity']
	
	fire['intensity'] -= ((64-_neighbor_intensity)/64.0)*random.uniform(0, SETTINGS['fire burn rate'])
	update_effect(fire)
	
	if fire['intensity'] <= 0:
		unregister_effect(fire)
	elif random.randint(0, 100) >= 99:
		create_light(fire['pos'], (255, 0, 255), 2*fire['intensity'], 0.1, fade=0.05)

def create_fire(pos, intensity=1):
	intensity = numbers.clip(intensity, 1, 8)
	
	_effect = {'type': 'fire',
			'color': tcod.Color(255, 69, 0),
			'pos': list(pos),
			'intensity': intensity,
			'callback': calculate_fire,
			'draw_callback': draw_fire}
	
	register_effect(_effect)

def calculate_all_effects():
	for effect in EFFECTS.values():
		effect['callback'](effect)

def update_effect(effect):
	_x = effect['pos'][0]-CAMERA_POS[0]
	_y = effect['pos'][1]-CAMERA_POS[1]
	
	if 0>_x>=MAP_WINDOW_SIZE[0] or 0>_y>=MAP_WINDOW_SIZE[1]:
		return False
	
	gfx.refresh_window_position(_x, _y)

def draw_effect(pos):
	if not EFFECT_MAP[pos[0]][pos[1]]:
		return False
	
	for effect in [EFFECTS[eid] for eid in EFFECT_MAP[pos[0]][pos[1]]]:
		_x = pos[0]-CAMERA_POS[0]
		_y = pos[1]-CAMERA_POS[1]
		
		effect['draw_callback']((_x, _y), effect)

def create_light(pos, color, brightness, shake, fade=0):
	LIGHTS.append({'pos': pos, 'color': color, 'brightness': brightness, 'shake': shake, 'fade': fade})

def has_splatter(position, what=None):
	#TODO: Make this into a dict so we can convert the position to a string and search that
	for splat in SPLATTERS:
		if splat['pos'] == position:
			if what and not what == splat['what']:
				continue
			
			return splat

def create_splatter(what, position, velocity=0, intensity=4):
	_splatter = has_splatter(tuple(position),what=what)
	_intensity = numbers.clip(random.random(), intensity*.05, intensity*.1)
	
	if not _splatter:
		_splatter = {'pos': list(position[:]),'what': what,'color': tcod.Color(0,0,0),'coef': _intensity}
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

def draw_splatter(position, render_at):
	_has_splatter = has_splatter(position)
	
	if not _has_splatter:
		return False
	
	gfx.tint_tile(render_at[0],render_at[1],_has_splatter['color'],_has_splatter['coef'])

def create_gib(life, icon, size, velocity):
	_gib = {'name': 'gib',
		'prefix': 'a',
		'type': 'magazine',
		'icon': icon,
		'flags': ['BLOODY'],
		'description': '%s\'s limb.' % ' '.join(life['name']),
		'size': '%sx1' % size,
		'material': 'flesh',
		'thickness': size}
	
	_i = items.create_item('gib', position=life['pos'][:], item=_gib)
	_i['velocity'] = [numbers.clip(velocity[0], -3, 3), numbers.clip(velocity[1], -3, 3), velocity[2]]
	
	logging.debug('Created gib.')