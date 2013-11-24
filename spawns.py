from globals import *

import items
import alife
import life

import logging
import random


SOLDIER_ITEMS = {'ALICE pack': 1,
                 'mp5': 1,
                 '9x19mm magazine': 1,
                 '9x19mm round': 15,
                 'frag grenade': 3}

LIFE_CLASSES = {'soldier': SOLDIER_ITEMS}


def generate_life(life_class, amount=1, group=False, spawn_chunks=[]):
	_group_members = []
	
	if spawn_chunks:
		_chunk_key = random.choice(spawn_chunks)
		_spawn = alife.chunks.get_chunk(_chunk_key)['pos']
	else:
		_spawn = get_spawn_point()
	
	for i in range(amount):
		_alife = life.create_life('human', map=WORLD_INFO['map'], position=[_spawn[0], _spawn[1], 2])
		
		for item in LIFE_CLASSES[life_class]:
			life.add_item_to_inventory(_alife, items.create_item(item))
		
		if group:
			if not _group_members:
				_alife['stats']['is_leader'] = True
				_group = alife.groups.create_group(_alife)
		
			_group_members.append(_alife)
	
	if group:
		for m1 in _group_members:
			if m1['id'] == _group_members[0]['id']:
				continue
			
			alife.groups.discover_group(m1, _group)
			alife.groups.add_member(_group_members[0], _group, m1['id'])
			alife.groups.add_member(m1, _group, m1['id'])
			m1['group'] = _group
			alife.groups.set_leader(m1, _group, _group_members[0]['id'])
	
			for m1 in _group_members:
				for m2 in _group_members:
					if m1 == m2:
						continue
					
					alife.stats.establish_trust(m1, m2['id'])
	
		alife.speech.inform_of_group_members(_group_members[0], None, _group)