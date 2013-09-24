from globals import *

import libtcodpy as tcod
import graphics as gfx
import life as lfe

import render_los
import numbers
import items
import tiles
import maps

import logging
import random
import numpy
import time
import sys

def register_effect(effect):
	effect['id'] = WORLD_INFO['effectid']
	EFFECTS[effect['id']] = effect
	EFFECT_MAP[effect['pos'][0]][effect['pos'][1]].append(effect['id'])
	
	WORLD_INFO['effectid'] += 1

def unregister_effect(effect):
	effect['unregister_callback'](effect)
	
	EFFECT_MAP[effect['pos'][0]][effect['pos'][1]].remove(effect['id'])
	del EFFECTS[effect['id']]

def draw_fire(pos, fire):
	_intensity = fire['intensity']/float(8)
	_rand_intensity = numbers.clip(_intensity-random.uniform(0, .2), 0, 1)
	
	gfx.tint_tile(pos[0], pos[1], fire['color'], _rand_intensity)

def calculate_fire(fire):
	_neighbor_intensity = 0
	_neighbor_lit = False
	
	for x in range(-1, 2):
		_x = fire['pos'][0]+x
		
		if _x<0 or _x>=MAP_SIZE[0]:
			continue
		
		for y in range(-1, 2):
			if not x and not y:
				continue
			
			_y = fire['pos'][1]+y
			
			if _y<0 or _y>=MAP_SIZE[1]:
				continue
			
			_effects = [EFFECTS[eid] for eid in EFFECT_MAP[_x][_y] if EFFECTS[eid]['type'] == 'fire']
			for effect in _effects:
				_neighbor_intensity += effect['intensity']
				
				if 'light' in effect:
					_neighbor_lit = True
			
			if not _effects:
				_tile = WORLD_INFO['map'][_x][_y][fire['pos'][2]]
				_raw_tile = tiles.get_raw_tile(_tile)
				
				_heat = tiles.get_flag(WORLD_INFO['map'][_x][_y][fire['pos'][2]], 'heat')
				_current_burn = int(round(fire['intensity']))
				_max_burn = int(round(_current_burn*.8))
				
				if tiles.flag(_tile, 'heat', numbers.clip(_heat+(fire['intensity']*.01), 0, 8))>=_raw_tile['burnable']:
					if _raw_tile['burnable'] and _max_burn:
						create_fire((_x, _y, fire['pos'][2]), intensity=random.randint(2, numbers.clip(2+_max_burn, 3, 8)))
	
	_intensity = ((64-_neighbor_intensity)/64.0)*random.uniform(0, SETTINGS['fire burn rate'])
	fire['intensity'] -= _intensity
	
	for life in [LIFE[life_id] for life_id in LIFE_MAP[fire['pos'][0]][fire['pos'][1]]]:
		lfe.burn(life, fire['intensity'])
	
	for item in items.get_items_at(fire['pos']):
		items.burn(item, fire['intensity'])
	
	update_effect(fire)
	
	if fire['intensity'] <= 0.25:
		unregister_effect(fire)
	
	if 'light' in fire:
		fire['light']['brightness'] -= numbers.clip(_intensity*.015, 0, 5)
	elif not _neighbor_lit:
		fire['light'] = create_light(fire['pos'], (255, 0, 255), .5*(fire['intensity']/8.0), 0.25)

def delete_fire(fire):
	tiles.flag(WORLD_INFO['map'][fire['pos'][0]][fire['pos'][1]][fire['pos'][2]], 'heat', False)
	tiles.flag(WORLD_INFO['map'][fire['pos'][0]][fire['pos'][1]][fire['pos'][2]], 'burnt', True)
	
	create_ash(fire['pos'])
	
	if 'light' in fire:
		WORLD_INFO['lights'].remove(fire['light'])

def create_fire(pos, intensity=1):
	intensity = numbers.clip(intensity, 1, 8)
	
	if not tiles.get_raw_tile(tiles.get_tile(pos))['burnable']:
		return False
	
	if tiles.get_flag(tiles.get_tile(pos), 'burnt'):
		return False
	
	_effect = {'type': 'fire',
	    'color': tcod.Color(255, 69, 0),
	    'pos': list(pos),
	    'intensity': intensity,
	    'callback': calculate_fire,
	    'draw_callback': draw_fire,
	    'unregister_callback': delete_fire}
	
	register_effect(_effect)

def draw_ash(pos, ash):
	gfx.tint_tile(pos[0], pos[1], ash['color'], ash['intensity'])

def delete_ash(ash):
	unregister_effect(ash)

def create_ash(pos):
	_color = random.randint(0, 25)
	_intensity = numbers.clip(_color/float(25), .3, 1)
	
	_effect = {'type': 'ash',
	    'color': tcod.Color(_color, _color, _color),
	    'intensity': _intensity, 
	    'pos': list(pos),
	    'callback': lambda x: 1==1,
	    'draw_callback': draw_ash,
	    'unregister_callback': delete_ash}
	
	register_effect(_effect)

def calculate_all_effects():
	for effect in EFFECTS.values():
		effect['callback'](effect)

def update_effect(effect):
	_x = effect['pos'][0]-CAMERA_POS[0]
	_y = effect['pos'][1]-CAMERA_POS[1]
	
	if _x<0 or _x>=MAP_WINDOW_SIZE[0]-1 or _y<0 or _y>=MAP_WINDOW_SIZE[1]-1:
		return False
	
	gfx.refresh_window_position(_x, _y)

def draw_effect(pos):
	if not EFFECT_MAP[pos[0]][pos[1]]:
		return False
	
	for effect in [EFFECTS[eid] for eid in EFFECT_MAP[pos[0]][pos[1]]]:
		_x = pos[0]-CAMERA_POS[0]
		_y = pos[1]-CAMERA_POS[1]
		
		effect['draw_callback']((_x, _y), effect)

def light_exists_at(pos):
	for light in WORLD_INFO['lights']:
		if light['pos'] == list(pos):
			return light
	
	return False

def create_light(pos, color, brightness, shake, fade=0, follow_pos=None):
	_light = {'pos': list(pos), 'color': color, 'brightness': brightness, 'shake': shake, 'fade': fade}
	
	if follow_pos:
		_light['pos'] = follow_pos
	
	WORLD_INFO['lights'].append(_light)
	
	return _light

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

def create_gib(life, icon, size, limb, velocity):
	_gib = {'name': 'gib',
		'prefix': 'a',
		'type': 'magazine',
		'icon': icon,
		'flags': ['BLOODY'],
		'description': '%s\'s %s.' % (limb, ' '.join(life['name'])),
		'size': '%sx1' % size,
		'material': 'flesh',
		'thickness': size}
	
	_i = items.get_item_from_uid(items.create_item('gib', position=life['pos'][:], item=_gib))
	_i['velocity'] = [numbers.clip(velocity[0], -3, 3), numbers.clip(velocity[1], -3, 3), velocity[2]]
	
	logging.debug('Created gib.')