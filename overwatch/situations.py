from globals import *

import graphics as gfx
import life as lfe

import artifacts
import language
import drawing
import numbers
import effects
import events
import spawns
import alife
import items
import maps
import core

import logging
import random


def form_scheme(force=False):
	if (WORLD_INFO['scheme'] or (WORLD_INFO['ticks']-WORLD_INFO['last_scheme_time'])<200) and not force or not SETTINGS['controlling']:
		return False
	
	_overwatch_mood = WORLD_INFO['overwatch']['mood']
	_player = LIFE[SETTINGS['controlling']]
	_player_situation = core.get_player_situation()
	_active_factions = set()
	_enemy_factions = set()
	
	for life in _player_situation['online_alife']:
		if not life['faction'] in _active_factions:
			_active_factions.add(life['faction'])
		
		if alife.factions.is_enemy(_player, life['id']) and not life['faction'] in _enemy_factions:
			_enemy_factions.add(life['faction'])
	
	_event_name = random.choice(['attract', 'capture'])
	_friendly_factions = list(_enemy_factions-_active_factions)
	_active_factions = list(_active_factions)
	_enemy_factions = list(_enemy_factions)
	
	if _event_name == 'attract':
		if _enemy_factions and not _friendly_factions:
			for enemy_faction in _enemy_factions:
				for enemy_of_enemy_faction in alife.factions.get_faction_enemies(enemy_faction):
					_nearest_group = alife.factions.get_nearest_group(enemy_of_enemy_faction, _player['pos'])
				
					if not _nearest_group:
						continue
					
					alife.factions.move_group_to(enemy_of_enemy_faction, _nearest_group, lfe.get_current_chunk_id(_player))
					
					WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']+250
	
	elif _event_name == 'capture' and _active_factions:
		_chosen_faction = random.choice(_active_factions)
		_chosen_group = random.choice(alife.factions.get_faction(_chosen_faction)['groups'])
		
		alife.factions.capture_territory(_chosen_faction, _chosen_group)
		
		WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']+550
	
	elif _event_name == 'anomaly' and _active_factions:# and not random.randint(0, 30):
		print 'HERE!!!!!!!!!!!!!!!!!!'
		
		if len(artifacts.get_active_fields())<3:
			_territory_id = artifacts.create_field()
			_territory = WORLD_INFO['territories'][_territory_id]
			
			for faction_name in _active_factions:
				_faction = WORLD_INFO['factions'][faction_name]
				
				for group_id in _faction['groups']:
					if random.randint(0, 1):
						continue
					
					_chunk_key = random.choice(_territory['chunk_keys'])
					maps.load_cluster_at_position_if_needed(WORLD_INFO['chunk_map'][_chunk_key]['pos'])
					
					print 'KEY', _chunk_key
					alife.factions.move_group_to(faction_name, group_id, _chunk_key)
			
			WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']+350
					
	WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']-120
	
	#if _overwatch_mood == 'hurt':
	#	if hurt_player(_player_situation):
	#		WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']
	#		
	#		return True
	#elif _overwatch_mood == 'intrigue':
	#	if intrigue_player(_player_situation):
	#		WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']
	#		
	#		return True	
	#elif _overwatch_mood == 'help':
	#	if help_player(_player_situation):
	#		WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']
	#		
	#		return True

def execute_scheme():
	if not WORLD_INFO['scheme']:
		return False
	
	_event = None
	
	for event in WORLD_INFO['scheme']:
		if event['time'] <= WORLD_INFO['ticks']:
			_event = event
			break
	
	if not _event:
		return False
	
	_situation = core.get_player_situation()
	_player = LIFE[SETTINGS['controlling']]
	
	if 'sound' in _event:
		alife.noise.create(_event['pos'], _event['volume'], _event['sound'][0], _event['sound'][1])
	
	if 'radio' in _event and _situation['has_radio']:
		gfx.message('%s: %s' % (_event['radio'][0], _event['radio'][1]), style='radio')
	
	if 'glitch' in _event:
		gfx.glitch_text(_event['glitch'], change_text_only=_event['change'])
	
	if 'life' in _event:
		_life = spawns.generate_life(_event['life']['type'], position=_event['life']['position'])[0]
		
		if 'injuries' in _event['life']:
			for limb in _event['life']['injuries']:
				lfe.add_wound(_life, limb, **_event['life']['injuries'][limb])
	
	if 'group' in _event:
		if 'stage' in _event:
			alife.groups.set_stage(LIFE[_event['member']], _event['group'], _event['stage'])
			
			if _event['stage'] == STAGE_RAIDING:
				alife.groups.raid(LIFE[_event['member']], _event['group'], _event['flags']['chunk_key'])
	
	WORLD_INFO['scheme'].remove(_event)

def intrigue_player(situation):
	_player = LIFE[SETTINGS['controlling']]
	_event_number = 0#random.randint(0, 1)
	
	#0: Cache drop (mid-game only: faction ordered)
	#1: Heli crash site (military)
	#2: Weather balloon (radio, PDA info: forecast)
	
	if _event_number == 1:
		_crash_pos = spawns.get_spawn_point_around(_player['pos'], area=150, min_area=90)
		
		events.create_heli_crash(_crash_pos, [])
		events.attract_tracked_alife_to(_crash_pos)
		core.record_dangerous_event(6)
	else:
		_land_pos = spawns.get_spawn_point_around(_player['pos'], area=160, min_area=90)
		_storage_items = [{'item': 'AK-74', 'rarity': 0.6},
		                  {'item': '5.45x39mm round', 'rarity': 0.6},
		                  {'item': '5.45x39mm round', 'rarity': 0.6},
		                  {'item': '5.45x39mm round', 'rarity': 0.6},
		                  {'item': '5.45x39mm round', 'rarity': 0.6},
		                  {'item': '5.45x39mm round', 'rarity': 0.6},
		                  {'item': '5.45x39mm round', 'rarity': 0.6},
		                  {'item': '5.45x39mm round', 'rarity': 0.6},
		                  {'item': '5.45x39mm magazine', 'rarity': 0.75}]
		_storage = [{'item': 'military crate', 'rarity': 1.0, 'spawn_list': _storage_items}]
		
		if situation['armed']:
			_group = spawns.generate_group('bandit', amount=3, spawn_chunks=[spawns.get_spawn_point_around(_land_pos, area=140, min_area=80, chunk_key=True)])
			
			for ai in _group:
				alife.brain.meet_alife(ai, _player)
				alife.stats.establish_hostile(ai, _player['id'])
			
			core.record_encounter(3, life_ids=[l['id'] for l in _group])
			events.attract_tracked_alife_to(_land_pos)
		
		events.create_cache_drop(_land_pos, _storage)
		core.record_dangerous_event(3)

def hurt_player(situation):
	_player = LIFE[SETTINGS['controlling']]
			
	return False

def help_player(situation):
	_player = LIFE[SETTINGS['controlling']]
