from globals import WORLD_INFO, SETTINGS, LIFE
from alife import factions

import graphics as gfx

import effects
import numbers
import timers
import items
import life

import random


def find_territory(has_owner=False):
	return random.choice([t for t in WORLD_INFO['territories'] if (not WORLD_INFO['territories'][t]['owner']) == has_owner])

def create_field():
	_territory_key = find_territory()
	_territory = WORLD_INFO['territories'][_territory_key]
	_territory['danger'] = random.choice(['burner'])
	_spawn_chunk_keys = [k for k in _territory['chunk_keys'] if WORLD_INFO['chunk_map'][k]['type'] == 'other']
	_territory['flags']['create_amount'] = numbers.clip(random.randint(3, 5), 0, len(_spawn_chunk_keys))
	
	return _territory_key

def get_active_fields():
	return [t for t in WORLD_INFO['territories'].values() if t['danger']]

def tick_fields():
	for territory in get_active_fields():
		_spawn_chunk_keys = [k for k in territory['chunk_keys'] if WORLD_INFO['chunk_map'][k]['type'] == 'other']
		
		if not 'create' in territory['flags'] or not territory['flags']['create']:
			if 'first_run' in territory['flags']:
				territory['flags']['create'] = random.randint(50, 60)
			else:
				territory['flags']['create'] = random.randint(150, 180)
				territory['flags']['first_run'] = True
				
				if SETTINGS['controlling'] and life.get_current_chunk_id(LIFE[SETTINGS['controlling']]) in _spawn_chunk_keys:
					gfx.message('The ground begins to shake...', style='alert')
				
				continue
		else:
			territory['flags']['create'] -= 1
				
			continue
		
		create_burner(_spawn_chunk_keys.pop(random.randint(0, len(_spawn_chunk_keys)-1)))
		territory['flags']['create_amount'] -= 1
		
		if not territory['flags']['create_amount']:
			territory['danger'] = None
			territory['flags']['create_amount'] = 0
			
			del territory['flags']['first_run']

def create_burner(chunk_key):
	_pos = random.choice(WORLD_INFO['chunk_map'][chunk_key]['ground'])[:]
	_pos.append(2)
	
	items.create_item('burner', position=_pos)
	effects.create_fire(_pos, intensity=8)
	effects.create_explosion(_pos, 4)
	
	print 'MAN CHECK THIS OUT!!!!!', chunk_key