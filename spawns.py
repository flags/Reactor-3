from globals import *

import worldgen
import items
import alife
import life

import logging
import random


SOLDIER_SPECIES = 'human'
SOLDIER_ITEMS = [{'kevlar jacket': 1},
                 {'ALICE pack': 1},
                 {'mp5': 1},
                 {'9x19mm magazine': 1},
                 {'9x19mm round': 15},
                 {'radio': 1},
                 {'frag grenade': 3}]
SOLDIER_STATS = {'firearms': 7+random.randint(0, 3),
                 'psychotic': True}
SOLDIER_BANNED_GOALS = ['discover']

BANDIT_SPECIES = 'human'
BANDIT_ITEMS = [{'white t-shirt': 1},
                {'leather backpack': 1},
                {'radio': 1},
                {'corn': 2},
                {'soda': 2},
                {'glock': 1},
                {'9x19mm magazine': 1},
                {'9x19mm round': 17}]
BANDIT_STATS = {'firearms': 3+random.randint(0, 2),
                'psychotic': True}

LONER_SPECIES = 'human'
LONER_ITEMS = [{'white t-shirt': 1},
               {'leather backpack': 1},
               {'radio': 1},
               {'corn': 2},
               {'soda': 2},
               {'glock': 1},
               {'9x19mm magazine': 1},
               {'9x19mm round': 17}]
LONER_STATS = {'firearms': 4+random.randint(0, 2)}

LIFE_CLASSES = {'soldier': {'species': SOLDIER_SPECIES,
                            'items': SOLDIER_ITEMS,
                            'stats': SOLDIER_STATS,
                            'banned_goals': SOLDIER_BANNED_GOALS},
                'bandit': {'species': SOLDIER_SPECIES,
                           'items': BANDIT_ITEMS,
                           'stats': BANDIT_STATS,
                           'banned_goals': []},
                'loner': {'species': LONER_SPECIES,
                          'items': LONER_ITEMS,
                          'stats': LONER_STATS,
                          'banned_goals': []},
                'feral dog': {'species': 'dog',
                              'items': [],
                              'stats': {},
                              'banned_goals': []}}


def generate_life(life_class, amount=1, spawn_chunks=[]):
	_life_species = LIFE_CLASSES[life_class]['species']
	_spawn_list = []
	
	if spawn_chunks:
		_chunk_key = random.choice(spawn_chunks)
		_spawn = random.choice(alife.chunks.get_chunk(_chunk_key)['ground'])
	else:
		_spawn = worldgen.get_spawn_point()
	
	for i in range(amount):
		if spawn_chunks:
			_chunk_key = random.choice(spawn_chunks)
			_spawn = random.choice(alife.chunks.get_chunk(_chunk_key)['ground'])
		
		_alife = life.create_life(_life_species, map=WORLD_INFO['map'], position=[_spawn[0], _spawn[1], 2])
		
		for item in LIFE_CLASSES[life_class]['items']:
			print item
			for i in range(item.values()[0]):
				life.add_item_to_inventory(_alife, items.create_item(item.keys()[0]))
		
		for stat in LIFE_CLASSES[life_class]['stats']:
			_alife['stats'][stat] = LIFE_CLASSES[life_class]['stats'][stat]
		
		for goal in LIFE_CLASSES[life_class]['banned_goals']:
			alife.planner.remove_goal(_alife, goal)
		
		_spawn_list.append(_alife)
		
	return _spawn_list

def generate_group(life_class, amount=3, group_motive='survival', spawn_chunks=[]):
	_group_members = generate_life(life_class, amount=amount, spawn_chunks=spawn_chunks)
	
	_group_members[0]['stats']['is_leader'] = True
	_group = alife.groups.create_group(_group_members[0])
	alife.groups.set_motive(_group_members[0], _group, 'crime')
	
	for m1 in _group_members:
		if m1['id'] == _group_members[0]['id']:
			continue
		
		alife.groups.discover_group(m1, _group)
		alife.groups.set_motive(m1, _group, 'crime')
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
	
	return _group_members