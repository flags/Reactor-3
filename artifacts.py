from globals import WORLD_INFO
from alife import factions

import items

import random


def find_territory(has_owner=False):
	return random.choice([t for t in WORLD_INFO['territories'] if (not WORLD_INFO['territories'][t]['owner']) == has_owner])

def create_field():
	_territory = WORLD_INFO['territories'][find_territory()]
	_territory['danger'] = True
	_field_type = random.choice(['burner'])
	_spawn_chunk_keys = [k for k in _territory['chunk_keys'] if WORLD_INFO['chunk_map'][k]['type'] == 'other']
	
	if _field_type == 'burner':
		_amount = int(round(len(_spawn_chunk_keys)*.75))
		
		for i in range(_amount):
			create_burner(_spawn_chunk_keys.pop(random.randint(0, len(_spawn_chunk_keys)-1)))

def create_burner(chunk_key):
	_pos = random.choice(WORLD_INFO['chunk_map'][chunk_key]['ground'])[:]
	_pos.append(2)
	items.create_item('burner', position=_pos)
	
	print 'MAN CHECK THIS OUT!!!!!', chunk_key