from globals import WORLD_INFO, SETTINGS, LIFE, ITEMS

import graphics as gfx

import language
import numbers
import drawing
import effects
import spawns
import alife
import core

import random


def create_heli_crash(pos, spawn_list):
	_pos = spawns.get_spawn_point_around(pos, area=10)
	_size = random.randint(4, 6)
	
	effects.create_explosion(_pos, _size)
	
	for n_pos in drawing.draw_circle(_pos, _size*2):
		if random.randint(0, 10):
			continue
		
		_n_pos = list(n_pos)
		_n_pos.append(2)
		
		effects.create_fire(_n_pos, intensity=8)
	
	core.record_dangerous_event(6)
		
def create_cache_drop(pos, spawn_list):
	_player = LIFE[SETTINGS['controlling']]
	
	_pos = spawns.get_spawn_point_around(pos, area=10)
	_direction = language.get_real_direction(numbers.direction_to(_player['pos'], _pos))
	
	gfx.message('You see something parachuting to the ground to the %s.' % _direction)

def spawn_life(life_type, position, event_time, **kwargs):
	_life = {'type': life_type, 'position': position[:]}
	_life.update(**kwargs)
	         
	WORLD_INFO['scheme'].append({'life': _life, 'time': event_time})

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
			
			_delay = (50*numbers.clip(_i, 0, 1))+(len(entry['text'])*2)*_i
			
			WORLD_INFO['scheme'].append({'glitch': entry['text'], 'change': _change, 'time': _time+_delay})
		else:
			WORLD_INFO['scheme'].append({'radio': [_source, entry['text']], 'time': _time})
		
		_i += 1
		_time += int(round(len(entry['text'])*1.25))

def attract_tracked_alife_to(pos):
	_chunk_key = alife.chunks.get_chunk_key_at(pos)
	
	for ai in [LIFE[i] for i in WORLD_INFO['overwatch']['tracked_alife']]:
		alife.movement.set_focus_point(ai, _chunk_key)
	
		logging.debug('[Overwatch]: Attracting %s to %s.' % (' '.join(ai['name']), _chunk_key))


FUNCTION_MAP = {'heli_crash': create_heli_crash,
                'cache_drop': create_cache_drop}