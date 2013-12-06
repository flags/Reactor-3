from globals import *

import items
import alife
import life

import logging
import random


SOLDIER_ITEMS = [{'kevlar jacket': 1},
                 {'ALICE pack': 1},
                 {'mp5': 1},
                 {'9x19mm magazine': 1},
                 {'9x19mm round': 15},
                 {'frag grenade': 3}]
SOLDIER_STATS = {'firearms': 7+random.randint(0, 3),
                 'psychotic': True}
SOLDIER_BANNED_GOALS = ['discover']

LIFE_CLASSES = {'soldier': {'items': SOLDIER_ITEMS,
                            'stats': SOLDIER_STATS,
                            'banned_goals': SOLDIER_BANNED_GOALS}}


def generate_life(life_class, amount=1, group=False, spawn_chunks=[]):
	_group_members = []
	
	if spawn_chunks:
		_chunk_key = random.choice(spawn_chunks)
		_spawn = random.choice(alife.chunks.get_chunk(_chunk_key)['ground'])
	else:
		_spawn = get_spawn_point()
	
	for i in range(amount):
		_alife = life.create_life('human', map=WORLD_INFO['map'], position=[_spawn[0], _spawn[1], 2])
		
		for item in LIFE_CLASSES[life_class]['items']:
			for i in range(item.values()[0]):
				life.add_item_to_inventory(_alife, items.create_item(item.keys()[0]))
		
		for stat in LIFE_CLASSES[life_class]['stats']:
			_alife['stats'][stat] = LIFE_CLASSES[life_class]['stats'][stat]
		
		for goal in LIFE_CLASSES[life_class]['banned_goals']:
			alife.planner.remove_goal(_alife, goal)
		
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