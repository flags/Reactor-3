from globals import *

import life as lfe

import language
import missions
import numbers
import weapons
import spawns
import alife
import items

import logging
import random


def generate():
	create_territories()
	create_faction('Dawn', ['dawn_scout', 'dawn_sentry'], enemies=['Bandits', 'Runners', 'Military'])
	create_faction('Runners', ['loner', 'loner_rifleman'], enemies=['Bandits', 'Dawn', 'Military'])
	create_faction('Loners', ['loner', 'loner_rifleman'], enemies=['Bandits', 'Military'])
	create_faction('ZES', ['zes_guard'], enemies=['Bandits', 'Military'])
	create_faction('Military', ['bandit'], enemies=['Runners', 'Dawn', 'Loners'])
	create_faction('Bandits', ['bandit'], enemies=['Runners', 'Dawn', 'Loners', 'Military'])
	create_faction('Dogs', ['bandit'], enemies=['Runners', 'Dawn', 'Loners', 'Military'])
	create_zes_export()
	create_fields()
	create_outposts()

def create_territories():
	for town in WORLD_INFO['refs']['towns']:
		_place_name = language.generate_place_name()
		
		WORLD_INFO['territories'][_place_name] = {'chunk_keys': town,
		                                          'owner': None,
		                                          'danger': False,
		                                          'flags': {}}
		
		logging.debug('Created territory: %s' % _place_name)

def get_territory(territory_name):
	return WORLD_INFO['territories'][territory_name]

def claim_territory(faction_name):
	_territory_name = random.choice([t for t in WORLD_INFO['territories'] if not WORLD_INFO['territories'][t]['owner']])
	_territory = get_territory(_territory_name)
	_territory['owner'] = faction_name
	_territory['groups'] = []
	_faction = get_faction(faction_name)
	_faction['territories'][_territory_name] = {'groups': []}
	
	logging.debug('%s has claimed %s.' % (faction_name, _territory_name))
	
	return _territory

def create_faction(name, life_types, friendlies=[], enemies=['Bandits']):
	WORLD_INFO['factions'][name] = {'members': [],
	                                'groups': [],
	                                'group_orders': {},
	                                'territories': {},
	                                'friendlies': friendlies,
	                                'enemies': enemies,
	                                'life_types': life_types,
	                                'flags': {}}
	
	logging.debug('Created faction: %s' % name)

def get_faction(faction_name):
	return WORLD_INFO['factions'][faction_name]

def get_faction_enemies(faction_name):
	return get_faction(faction_name)['enemies']

def is_enemy(life, life_id):
	if not life['faction'] or not LIFE[life_id]['faction']:
		return False
	
	_faction = get_faction(life['faction'])
	_target_faction_name = LIFE[life_id]['faction']
	
	return _target_faction_name in _faction['enemies']

def is_faction_enemy(life, faction_name):
	if not life['faction']:
		return False
	
	_faction = get_faction(life['faction'])
	
	return faction_name in _faction['enemies']

def add_member(faction_name, life_id):
	_faction = get_faction(faction_name)
	
	if life_id in _faction['members']:
		return False
	
	_faction['members'].append(life_id)
	
	LIFE[life_id]['faction'] = faction_name

def add_group(faction_name, group_id):
	for life_id in alife.groups.get_group({}, group_id)['members']:
		add_member(faction_name, life_id)
	
	_faction = get_faction(faction_name)
	_faction['groups'].append(group_id)
	
	for territory_name in _faction['territories']:
		_territory = _faction['territories'][territory_name]
		
		if not _territory['groups']:
			patrol_territory(faction_name, group_id, territory_name)
			
			break

def get_group_order(faction_name, group_id):
	_faction = get_faction(faction_name)
	
	if group_id in _faction['group_orders']:
		return _faction['group_orders'][group_id]
	
	return None

def set_group_order(faction_name, group_id, order):
	_faction = get_faction(faction_name)
	_faction['group_orders'][group_id] = {'order': order,
	                                      'flags': {}}

def clear_group_order(faction_name, group_id):
	_faction = get_faction(faction_name)
	
	del _faction['group_orders'][group_id]

def get_free_groups(faction_name):
	_faction = get_faction(faction_name)
	
	return list(set(_faction['groups']) - set(_faction['group_orders']))

def get_nearest_group(faction_name, pos, free_only=True, max_distance=250):
	_faction = get_faction(faction_name)
	_nearest_group = {'group_id': None, 'distance': max_distance}
	
	for group_id in _faction['groups']:
		if free_only and group_id in _faction['group_orders']:
			continue
		
		for member_id in alife.groups.get_group({}, group_id)['members']:
			_distance = numbers.distance(LIFE[member_id]['pos'], pos)
			
			if _distance < _nearest_group['distance']:
				_nearest_group['group_id'] = group_id
				_nearest_group['distance'] = _distance
	
	return _nearest_group['group_id']

def patrol_territory(faction_name, group_id, territory_name):
	_faction = get_faction(faction_name)
	_territory = _faction['territories'][territory_name]
	_territory['groups'].append(group_id)
	
	#alife.groups.focus_on

def capture_territory(faction_name, group_id):
	if faction_name == 'ZES':
		return False
	
	_closest_territory = {'distance': 0, 'chunk_key': None, 'territory_id': None}
	_group_center = None
	
	for member_id in alife.groups.get_group({}, group_id)['members']:
		_member = LIFE[member_id]
		
		if not _group_center:
			_group_center = _member['pos'][:]
			
			continue
		
		_group_center = numbers.lerp_velocity(_group_center, _member['pos'], .5)
	
	for territory_id in WORLD_INFO['territories']:
		_territory = WORLD_INFO['territories'][territory_id]
		
		if _territory['owner'] == faction_name:
			continue
		
		#TODO: Pre-compute?
		_nearest_chunk = alife.chunks.get_nearest_chunk_in_list(_group_center, _territory['chunk_keys'], include_distance=True)
		
		if not _closest_territory['chunk_key'] or _nearest_chunk['distance'] < _closest_territory['distance']:
			_closest_territory['distance'] = _nearest_chunk['distance']
			_closest_territory['chunk_key'] = _nearest_chunk['chunk_key']
			_closest_territory['territory_id'] = territory_id
	
	for member_id in alife.groups.get_group({}, group_id)['members']:
		_member = LIFE[member_id]
		
		missions.create_mission_for_self(_member, 'travel_to', chunk_key=_closest_territory['chunk_key'])
		#missions.create_mission_for_self(_member, 'capture_territory', territory_id=_closest_territory['territory_id'])
		set_group_order(faction_name, group_id, 'travel_to')

def move_group_to(faction_name, group_id, chunk_key):
	for member_id in alife.groups.get_group({}, group_id)['members']:
		_member = LIFE[member_id]
		
		if not missions.has_mission_with_name(_member, 'travel_to'):
			missions.create_mission_for_self(_member, 'travel_to', chunk_key=chunk_key)
			set_group_order(faction_name, group_id, 'travel_to')

def resupply(faction_name, group_id, chunk_key):
	for member_id in alife.groups.get_group({}, group_id)['members']:
		_member = LIFE[member_id]
		
		missions.create_mission_for_self(_member, 'travel_to', chunk_key=chunk_key)
		#missions.create_mission_for_self(_member, 'resupply', chunk_key=chunk_key)
		set_group_order(faction_name, group_id, 'travel_to')

def manage_faction_groups():
	for faction_name in WORLD_INFO['factions']:
		_faction = get_faction(faction_name)
		
		for group_id in _faction['groups']:
			_group_order = get_group_order(faction_name, group_id)
			
			if not _group_order:
				continue
			
			for member_id in alife.groups.get_group({}, group_id)['members']:
				if missions.has_mission_with_name(LIFE[member_id], _group_order['order']):
					break
			else:
				continue
			
			clear_group_order(faction_name, group_id)

def create_zes_export():
	_zes_camp_chunk_key = random.choice(claim_territory('ZES')['chunk_keys'])
	
	spawns.generate_group('zes_guard', faction='ZES', amount=random.randint(3, 4), spawn_chunks=[_zes_camp_chunk_key])

def create_fields():
	_lower_half_chunk_keys = alife.chunks.get_chunks_in_range(0, 1, .6, 1)
	
	spawns.generate_group('loner', faction='Loners', amount=random.randint(3, 4), spawn_chunks=random.sample(_lower_half_chunk_keys, 1))
	spawns.generate_group('bandit', faction='Bandits', amount=random.randint(3, 4), spawn_chunks=random.sample(_lower_half_chunk_keys, 1))

def create_outposts():
	for outpost_chunks in WORLD_INFO['refs']['outposts']:
		spawns.generate_group('soldier', faction='Military', amount=random.randint(1, 2), spawn_chunks=outpost_chunks)
		spawns.generate_group('soldier_riflemen', faction='Military', amount=random.randint(1, 2), spawn_chunks=outpost_chunks)

def control_loners():
	_loners = get_faction('Loners')
	
	for squad in _loners['groups']:
		for member in [LIFE[i] for i in squad]:
			#print member['name'], alife.groups.get_stage(member, member['group'])
			if not alife.groups.is_leader(member, member['group'], member['id']):
				continue
		
			alife.groups.set_stage(member, member['group'], STAGE_RAIDING)
			alife.groups.flag(member, member['group'], 'raid_chunk', WORLD_INFO['refs']['outposts'][0][0])

def control_zes():
	_zes = get_faction('ZES')
	
	if not 'intro_created' in _zes['flags'] and _zes['members'] and SETTINGS['controlling']:
		_zes = get_faction('ZES')
		_zes['flags']['intro_created'] = True
		_item_uid = weapons.spawn_and_arm('glock', '9x19mm magazine', '9x19mm round', 17)
		_kill_target = get_faction('Bandits')['members'][0]
		_kill_target_direction = numbers.distance(LIFE[_zes['members'][0]]['pos'], LIFE[_kill_target]['pos'])
		_quest_item_uid = lfe.get_inventory_item_matching(LIFE[_kill_target], {'type': 'radio'})
		_mission = missions.create_mission('zes_glock', target=SETTINGS['controlling'],
		                                   item_uid=_item_uid,
		                                   quest_item_uid=_quest_item_uid,
		                                   deliver_target=_zes['members'][0],
		                                   kill_target=_kill_target,
		                                   location=lfe.get_current_chunk_id(LIFE[_kill_target]))
		
		lfe.add_item_to_inventory(LIFE[_zes['members'][0]], _item_uid)
		alife.brain.meet_alife(LIFE[_zes['members'][0]], LIFE[SETTINGS['controlling']])
		alife.memory.create_question(LIFE[_zes['members'][0]],
		                             SETTINGS['controlling'],
		                             'zes_intro',
		                             kill_target_name=' '.join(LIFE[_kill_target]['name']),
		                             kill_target_direction=language.get_real_direction(_kill_target_direction))
		missions.remember_mission(LIFE[_zes['members'][0]], _mission)
		missions.activate_mission(LIFE[_zes['members'][0]], '1')
	
	#for group_id in _zes['groups']:
	#	pass
	#	#for member in [LIFE[i] for i in alife.groups.get_group({}, group_id)['members']]:
	
	#for group_id in _loners['groups']:
	#	for member in [LIFE[i] for i in squad]:
	#		#print member['name'], alife.groups.get_stage(member, member['group'])
	#		if not alife.groups.is_leader(member, member['group'], member['id']):
	#			continue
	#	
	#		alife.groups.set_stage(member, member['group'], STAGE_RAIDING)
	#		alife.groups.flag(member, member['group'], 'raid_chunk', WORLD_INFO['refs']['outposts'][0][0])

def direct():
	#for faction_name in WORLD_INFO['factions']:
	#if faction_name == 'Loners':
	#control_loners()
	manage_faction_groups()
	control_zes()