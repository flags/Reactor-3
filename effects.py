from globals import *

import libtcodpy as tcod
import graphics as gfx
import life as lfe

import render_los
import bad_numbers
import weather
import alife
import items
import tiles
import maps

import logging
import random
import numpy
import time
import sys

def register_effect(effect):
	effect['id'] = str(WORLD_INFO['effectid'])
	EFFECTS[effect['id']] = effect
	EFFECT_MAP[effect['pos'][0]][effect['pos'][1]].append(effect['id'])
	
	WORLD_INFO['effectid'] += 1

def unregister_effect(effect, remove_from_effect_map=True):
	if effect['unregister_callback']:
		effect['unregister_callback'](effect)
	
	if remove_from_effect_map:
		EFFECT_MAP[effect['pos'][0]][effect['pos'][1]].remove(effect['id'])
	
	del EFFECTS[effect['id']]

def create_fire(pos, intensity=1):
	intensity = bad_numbers.clip(intensity, 1, 8)
	
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

def draw_fire(pos, fire):
	_intensity = fire['intensity']/float(8)
	_rand_intensity = bad_numbers.clip(_intensity-random.uniform(0, .2), 0, 1)
	
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
			
			maps.load_cluster_at_position_if_needed((_x, _y, fire['pos'][2]))
			
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
				_max_burn = int(round(_current_burn*.23))
				
				if tiles.flag(_tile, 'heat', bad_numbers.clip(_heat+(fire['intensity']*.8), 0, 8))>=_raw_tile['burnable']:
					if _raw_tile['burnable'] and _max_burn:
						create_fire((_x, _y, fire['pos'][2]), intensity=random.randint(1, bad_numbers.clip(1+_max_burn, 2, 8)))
	
	_intensity = ((64-_neighbor_intensity)/64.0)*random.uniform(0, SETTINGS['fire burn rate'])
	fire['intensity'] -= _intensity
	
	if random.randint(0, 1):
		_pos = fire['pos'][:2]
		_pos.append(2)
		
		create_smoke(_pos, direction=random.randint(0, 369), speed=random.uniform(0.3, 0.85), age=0.2, max_opacity=0.9, decay=0.03)
	
	for life in [LIFE[life_id] for life_id in LIFE_MAP[fire['pos'][0]][fire['pos'][1]]]:
		lfe.burn(life, fire['intensity'])
	
	for item in items.get_items_at(fire['pos']):
		items.burn(item, fire['intensity'])
	
	update_effect(fire)
	
	if fire['intensity'] <= 0.25:
		unregister_effect(fire)
	
	if 'light' in fire:
		fire['light']['brightness'] -= bad_numbers.clip(_intensity*.015, 0, 5)
	elif not _neighbor_lit:
		fire['light'] = create_light(fire['pos'], (255, 69, 0), 17*(fire['intensity']/8.0), 0.25)

def delete_fire(fire):
	tiles.flag(WORLD_INFO['map'][fire['pos'][0]][fire['pos'][1]][fire['pos'][2]], 'heat', False)
	tiles.flag(WORLD_INFO['map'][fire['pos'][0]][fire['pos'][1]][fire['pos'][2]], 'burnt', True)
	
	create_ash(fire['pos'])
	
	if 'light' in fire:
		delete_light(fire['light'])

def create_ash(pos):
	_color = random.randint(0, 25)
	_intensity = bad_numbers.clip(_color/float(25), .3, 1)
	
	_effect = {'type': 'ash',
	    'color': tcod.Color(_color, _color, _color),
	    'intensity': _intensity, 
	    'pos': list(pos),
	    'callback': lambda x: 1==1,
	    'draw_callback': draw_ash,
	    'unregister_callback': lambda ash: unregister_effect(ash)}
	
	register_effect(_effect)

def draw_ash(pos, ash):
	gfx.tint_tile(pos[0], pos[1], ash['color'], ash['intensity'])

def clear_effect(effect):
	if gfx.position_is_in_frame(effect['pos']):
		gfx.refresh_view_position(effect['pos'][0]-CAMERA_POS[0], effect['pos'][1]-CAMERA_POS[1], 'map')

def create_explosion(pos, force):
	alife.noise.create(pos, force*100, 'an explosion', 'a low rumble', skip_on_visual=False)
	
	create_light(pos, (255, 69, 0), force*6, 1, fade=3)
	create_smoke_cloud(pos,
	                   force*6,
	                   age=.8,
	                   factor_distance=True)

	for i in range(random.randint(1, 3)):
		create_smoke_streamer(pos,
		                      3+random.randint(0, 2),
		                      (force*2)+random.randint(3, 6),
		                      color=tcod.color_lerp(tcod.gray, tcod.crimson, random.uniform(0.1, 0.3)))

def create_smoke(pos, color=tcod.gray, age=0, grow=0.1, decay=0.1, direction=-1, speed=0.3, max_opacity=.75, interp_wind=True):
	_intensity = random.uniform(max_opacity*.25, max_opacity)
	_color = tcod.color_lerp(color, tcod.white, random.uniform(0, 0.3))
	
	if direction == -1:
		_velocity = [random.uniform(-speed, speed), random.uniform(-speed, speed), 0]
	else:
		_velocity = bad_numbers.velocity(direction, speed)
	
	_effect = {'type': 'smoke',
	           'color': _color,
	           'intensity': _intensity*age,
	           'max_intensity': _intensity,
	           'decay': decay,
	           'grow': grow,
	           'disappear': False,
	           'pos': list(pos),
	           'float_pos': list(pos),
	           'interp_wind': interp_wind,
	           'velocity': [_velocity[0], _velocity[1], _velocity[2]],
	           'callback': process_smoke,
	           'draw_callback': draw_smoke,
	           'unregister_callback': clear_effect}
	
	register_effect(_effect)

def create_smoke_cloud(pos, size, color=tcod.gray, age=0, factor_distance=False):
	if not gfx.position_is_in_frame(pos):
		return False
	
	for new_pos in render_los.draw_circle(pos[0], pos[1], size):
		if not gfx.position_is_in_frame(new_pos):
			continue
		 
		maps.load_cluster_at_position_if_needed(new_pos)
		 
		if not alife.sight._can_see_position(pos, new_pos, distance=False):
			continue
		
		_age_mod = 1
		if factor_distance:
			_age_mod = 1-bad_numbers.clip(bad_numbers.distance(pos, new_pos)/float(size), 0.1, 1)
		
		create_smoke(new_pos, color=color, age=age*_age_mod)

def create_smoke_streamer(pos, size, length, color=tcod.gray):
	_direction = random.randint(0, 359)
	_end_velocity = bad_numbers.velocity(_direction, length)
	_end_pos = [int(round(pos[0]+_end_velocity[0])), int(round(pos[1]+_end_velocity[1]))]
	
	for new_pos in render_los.draw_line(pos[0], pos[1], _end_pos[0], _end_pos[1]):
		_new_pos = [new_pos[0], new_pos[1], pos[2]]
		create_smoke_cloud(_new_pos, size, age=-bad_numbers.distance(pos, new_pos)/float(length), color=color)

def process_smoke(smoke):
	if smoke['disappear']:
		smoke['intensity'] -= smoke['decay']
	else:
		if smoke['intensity'] < smoke['max_intensity']:
			smoke['intensity'] += smoke['grow']
		else:
			smoke['disappear'] = True
	
	if smoke['intensity'] < 0 and smoke['disappear']:
		unregister_effect(smoke)
		
		return False
	
	if smoke['interp_wind']:
		smoke['velocity'] = bad_numbers.lerp_velocity(smoke['velocity'], weather.get_wind_velocity(), 0.05)
	
	smoke['float_pos'][0] += smoke['velocity'][0]
	smoke['float_pos'][1] += smoke['velocity'][1]
	
	_in_frame = gfx.position_is_in_frame(smoke['pos'])
	_old_pos = smoke['pos'][:2]
	
	if _in_frame:
		gfx.refresh_view_position(smoke['pos'][0]-CAMERA_POS[0], smoke['pos'][1]-CAMERA_POS[1], 'map')
	
	EFFECT_MAP[smoke['pos'][0]][smoke['pos'][1]].remove(smoke['id'])
	
	smoke['pos'] = [int(round(smoke['float_pos'][0])), int(round(smoke['float_pos'][1]))]
	
	if _in_frame and not smoke['pos'] == _old_pos:
		gfx.refresh_view_position(smoke['pos'][0]-CAMERA_POS[0], smoke['pos'][1]-CAMERA_POS[1], 'map')
	
	if smoke['pos'][0]<0 or smoke['pos'][1]<0 or smoke['pos'][0]>=MAP_SIZE[0]-1 or smoke['pos'][1]>=MAP_SIZE[1]-1:
		unregister_effect(smoke, remove_from_effect_map=False)
		return False
	
	EFFECT_MAP[smoke['pos'][0]][smoke['pos'][1]].append(smoke['id'])

def draw_smoke(pos, smoke):
	gfx.tint_tile(pos[0], pos[1], smoke['color'], bad_numbers.clip(smoke['intensity'], 0, smoke['max_intensity']))

def create_smoker(pos, time, color=tcod.gray):
	_color = random.randint(200, 205)
	_pos = list(pos)
	
	if len(_pos)<3:
		_pos.append(2)
	
	_effect = {'type': 'vapor',
	           'age': 0,
	           'age_max': time,
	           'max_intensity': 0.3,
	           'color': color,
	           'pos': _pos,
	           'callback': process_smoker,
	           'draw_callback': None,
	           'unregister_callback': None}
	
	register_effect(_effect)

def process_smoker(smoker):
	if smoker['age'] >= smoker['age_max']:
		unregister_effect(smoker)
		return False
	
	smoker['age'] += 1
	
	create_smoke(smoker['pos'], color=smoker['color'], decay=0.03, direction=random.randint(0, 359))

def create_vapor(pos, time, intensity):
	_color = random.randint(200, 205)
	
	_effect = {'type': 'vapor',
	           'age': time*(1-intensity),
	           'age_max': time,
	           'max_intensity': 0.3,
	           'color': tcod.Color(_color, _color, _color),
	           'pos': list(pos),
	           'callback': process_vapor,
	           'draw_callback': draw_vapor,
	           'unregister_callback': None}
	
	register_effect(_effect)

def process_vapor(vapor):
	if vapor['age'] >= vapor['age_max']:
		unregister_effect(vapor)
		return False
	
	vapor['age'] += 1

def draw_vapor(pos, vapor):
	gfx.tint_tile(pos[0], pos[1], vapor['color'], bad_numbers.clip(vapor['max_intensity']*(1-(vapor['age']/float(vapor['age_max']))), 0, vapor['max_intensity']))

#def create_particle(pos, color, velocity):
#	_effect = {'type': 'particle',
#	           'color': color,
#	           'pos': pos,
#	           'velocity': velocity,
#	           'callback': calculate_particle,
#	           'draw_callback': draw_particle,
#	           'unregister_callback': delete_particle}
#	
#	register_effect(_effect)

def calculate_all_effects():
	_remove_lights = []
	
	for effect in list(EFFECTS.values()):
		effect['callback'](effect)
	
	for light in WORLD_INFO['lights']:
		if light['fade']:
			light['brightness'] -= light['fade']
		
		if light['brightness'] <= 0:
			_remove_lights.append(light)

	for light in _remove_lights:
		delete_light(light)

def update_effect(effect):
	_x = effect['pos'][0]-CAMERA_POS[0]
	_y = effect['pos'][1]-CAMERA_POS[1]
	_view = gfx.get_view_by_name('map')
	
	if _x<0 or _x>=_view['draw_size'][0]-1 or _y<0 or _y>=_view['draw_size'][1]-1:
		return False
	
	gfx.refresh_view_position(_x, _y, 'map')

def draw_effect(pos):
	if not EFFECT_MAP[pos[0]][pos[1]]:
		return False
	
	for effect in [EFFECTS[eid] for eid in EFFECT_MAP[pos[0]][pos[1]]]:
		_x = pos[0]-CAMERA_POS[0]
		_y = pos[1]-CAMERA_POS[1]
		
		if effect['draw_callback']:
			effect['draw_callback']((_x, _y), effect)

def light_exists_at(pos):
	for light in WORLD_INFO['lights']:
		if light['pos'] == list(pos):
			return light
	
	return False

def create_light(pos, color, brightness, shake, fade=0, follow_item=None):
	_light = {'pos': list(pos), 'color': list(color), 'brightness': brightness, 'shake': shake, 'fade': fade}
	
	_light['color'][0] *= _light['brightness']/50.0
	_light['color'][1] *= _light['brightness']/50.0
	_light['color'][2] *= _light['brightness']/50.0
	
	if follow_item:
		_light['follow_item'] = follow_item
	
	WORLD_INFO['lights'].append(_light)
	
	return _light

def delete_light(light):
	WORLD_INFO['lights'].remove(light)

def delete_light_at(pos):
	_light = light_exists_at(pos)
	
	if not _light:
		logging.warning('Cannot remove light: No light exists at position %s, %s' % (pos[0], pos[1]))
		return False
	
	delete_light(_light)

def has_splatter(position, what=None):
	#TODO: Make this into a dict so we can convert the position to a string and search that
	for splat in SPLATTERS:
		if splat['pos'] == position:
			if what and not what == splat['what']:
				continue
			
			return splat

def create_splatter(what, position, velocity=[0, 0], intensity=4):
	_intensity = bad_numbers.clip(random.random(), intensity*.05, intensity*.1)
	
	#if not _splatter:
	_splatter = {'pos': list(position[:]), 'what': what, 'color': tcod.Color(0, 0, 0), 'coef': _intensity}
	
	if velocity[0]>0:
		_splatter['pos'][0] += random.randint(0, bad_numbers.clip(int(round(velocity[0])), 0, 2))
	elif velocity[0]<0:
		_splatter['pos'][0] -= random.randint(0, bad_numbers.clip(-int(round(velocity[0])), 0, 2))
	
	if velocity[1]>0:
		_splatter['pos'][1] += random.randint(0, bad_numbers.clip(int(round(velocity[1])), 0, 2))
	elif velocity[1]<0:
		_splatter['pos'][1] -= random.randint(0, bad_numbers.clip(-int(round(velocity[1])), 0, 2))
 
	_has_splatter = has_splatter(tuple(_splatter['pos']), what=what)
	
	if _has_splatter:
		if what == 'blood':
			_has_splatter['color'].r = 150
		else:
			_has_splatter['coef'] += 0.3
			_has_splatter['coef'] = bad_numbers.clip(_has_splatter['coef'],0,1)
		
		return True
	
	_splatter['pos'] = tuple(_splatter['pos'])
	SPLATTERS.append(_splatter)

def draw_splatter(position, render_at):
	_has_splatter = has_splatter(position)
	
	if not _has_splatter:
		return False
	
	gfx.tint_tile(render_at[0],render_at[1],_has_splatter['color'],_has_splatter['coef'])

def create_gib(life, icon, size, limb, velocity, color=(tcod.white, None)):
	_gib = {'name': 'gib',
		'prefix': 'a',
		'type': 'magazine',
		'icon': icon,
		'flags': ['BLOODY'],
		'description': '%s\'s %s.' % (' '.join(life['name']), limb),
		'size': '%sx1' % size,
		'material': 'flesh',
		'thickness': size,
		'color': color}
	
	_i = items.get_item_from_uid(items.create_item('gib', position=life['pos'][:], item=_gib))
	_i['velocity'] = [bad_numbers.clip(velocity[0], -3, 3), bad_numbers.clip(velocity[1], -3, 3), velocity[2]]
	
	logging.debug('Created gib.')