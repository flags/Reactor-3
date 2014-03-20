from globals import *

import life as lfe

import language
import spawns
import alife

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
		                                          'owner': None}
		
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

def is_enemy(life, life_id):
	if not life['faction'] or not LIFE[life_id]['faction']:
		return False
	
	_faction = get_faction(life['faction'])
	_target_faction_name = LIFE[life_id]['faction']
	
	return _target_faction_name in _faction['enemies']

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

def patrol_territory(faction_name, group_id, territory_name):
	_faction = get_faction(faction_name)
	_territory = _faction['territories'][territory_name]
	_territory['groups'].append(group_id)
	
	#alife.groups.focus_on

def create_zes_export():
	#_zes = get_faction('ZES')
	#alife.memory.create_question(LIFE[_zes['members'][0]], SETTINGS['controlling'], 'zes_intro')
	#_zes_camp_chunk_key = random.choice(alife.chunks.get_chunks_in_range(.2, .8, .8, 1))
	_zes_camp_chunk_key = random.choice(claim_territory('ZES')['chunk_keys'])
	
	spawns.generate_group('zes_guard', faction='ZES', amount=random.randint(3, 4), spawn_chunks=[_zes_camp_chunk_key])

def create_fields():
	_lower_half_chunk_keys = alife.chunks.get_chunks_in_range(0, 1, .6, 1)
	
	spawns.generate_group('loner', faction='Loners', amount=random.randint(3, 4), spawn_chunks=random.sample(_lower_half_chunk_keys, 1))
	spawns.generate_group('bandit', faction='Bandits', amount=random.randint(3, 4), spawn_chunks=random.sample(_lower_half_chunk_keys, 1))

def create_outposts():
	for outpost_chunks in WORLD_INFO['refs']['outposts']:
		spawns.generate_group('soldier', faction='Military', amount=random.randint(3, 4), spawn_chunks=outpost_chunks)

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
		
		alife.brain.meet_alife(LIFE[_zes['members'][0]], LIFE[SETTINGS['controlling']])
		alife.memory.create_question(LIFE[_zes['members'][0]], SETTINGS['controlling'], 'zes_intro')
	
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
	control_zes()