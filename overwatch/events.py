from globals import WORLD_INFO, SETTINGS, LIFE, ITEMS

import graphics as gfx
import libtcodpy as tcod

import artifacts
import language
import bad_numbers
import drawing
import effects
import spawns
import items
import alife
import maps
from . import core

import logging
import random


def create_heli_crash(pos, spawn_list):
	_size = random.randint(4, 6)
	
	effects.create_explosion(pos, _size)
	
	for n_pos in drawing.draw_circle(pos, _size*2):
		if random.randint(0, 10):
			continue
		
		_n_pos = list(n_pos)
		_n_pos.append(2)
		
		effects.create_fire(_n_pos, intensity=8)
		
def create_cache_drop(pos, spawn_list):
	_player = LIFE[SETTINGS['controlling']]
	_pos = spawns.get_spawn_point_around(pos, area=10)
	_direction = language.get_real_direction(bad_numbers.direction_to(_player['pos'], _pos))
	
	for container in spawn_list:
		if not container['rarity']>random.uniform(0, 1.0):
			continue
		
		_c = items.create_item(container['item'], position=[_pos[0], _pos[1], 2])
		
		for _inside_item in container['spawn_list']:
			if _inside_item['rarity']<=random.uniform(0, 1.0):
				continue
			
			_i = items.create_item(_inside_item['item'], position=[_pos[0], _pos[1], 2])
			
			if not items.can_store_item_in(_i, _c):
				items.delete_item(_i)
				
				continue
			
			items.store_item_in(_i, _c)
	
	effects.create_smoker(_pos, 300, color=tcod.orange)
	
	gfx.message('You see something parachuting to the ground to the %s.' % _direction, style='event')

def create_anomaly_field(situation, y_min=0):
	return artifacts.create_field(y_min=y_min)

def spawn_life(life_type, position, event_time, **kwargs):
	_life = {'type': life_type, 'position': position[:]}
	_life.update(**kwargs)
	         
	WORLD_INFO['scheme'].append({'life': _life, 'time': WORLD_INFO['ticks']+event_time})

def order_group(life, group_id, stage, event_time, **kwargs):
	WORLD_INFO['scheme'].append({'group': group_id,
	                             'member': life['id'],
	                             'stage': stage,
	                             'flags': kwargs,
	                             'time': WORLD_INFO['ticks']+event_time})

def broadcast(messages, event_time, glitch=False):
	_time = WORLD_INFO['ticks']+event_time
	_i = 0
	
	for entry in messages:
		if 'source' in entry:
			_source = entry['source']
		else:
			_source = '???'		
		
		
		if glitch:
			if 'change_only' in entry:
				_change = entry['change_only']
			else:
				_change = False
			
			_delay = (50*bad_numbers.clip(_i, 0, 1))+(len(entry['text'])*2)*_i
			
			WORLD_INFO['scheme'].append({'glitch': entry['text'], 'change': _change, 'time': _time+_delay})
		else:
			WORLD_INFO['scheme'].append({'radio': [_source, entry['text']], 'time': _time})
			
		_time += int(round(len(entry['text'])*1.25))
		_i += 1

def sound(near_text, far_text, position, volume, time):
	WORLD_INFO['scheme'].append({'sound': (near_text, far_text), 'pos': position, 'time': WORLD_INFO['ticks']+time, 'volume': volume})

def attract_tracked_alife_to(pos):
	_chunk_key = alife.chunks.get_chunk_key_at(pos)
	
	for ai in [LIFE[i] for i in WORLD_INFO['overwatch']['tracked_alife']]:
		alife.movement.set_focus_point(ai, _chunk_key)
	
		logging.debug('[Overwatch]: Attracting %s to %s.' % (' '.join(ai['name']), _chunk_key))


FUNCTION_MAP = {'heli_crash': create_heli_crash,
                'cache_drop': create_cache_drop}