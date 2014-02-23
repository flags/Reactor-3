from globals import *

import graphics as gfx
import life as lfe

import language
import numbers
import effects
import spawns
import alife
import items

import logging
import random


def create_heli_crash(kind):
	while 1:
		chunk_key = random.choice(WORLD_INFO['chunk_map'])
		
		_walkable = alife.chunks.get_walkable_areas(chunk_key)
		if not _walkable:
			continue
		
def drop_cache(item_names):
	while 1:
		_chunk_key = random.choice(WORLD_INFO['chunk_map'].keys())
		_chunk = alife.chunks.get_chunk(_chunk_key)
		
		if _chunk['type'] == 'other':
			break
	
	for item in item_names:
		_pos = random.choice(_chunk['ground'])
		_item = ITEMS[items.create_item(item, position=[_pos[0], _pos[1], 2])]
		
		for life in LIFE.values():
			lfe.memory(life, 'cache_drop', chunk_key=_chunk_key)
			#alife.survival.add_needed_item(life,
			#                               {'pos': _item['pos'][:]},
			#                               satisfy_if=alife.action.make_small_script(function='always'),
			#                               satisfy_callback=alife.action.make_small_script(function='consume'))
			#alife.brain.remember_item(life, _item)
	
	gfx.message('You see something parachuting to the ground.')
	print _chunk['pos']

def get_player_situation():
	if not SETTINGS['controlling']:
		return False
	
	_life = LIFE[SETTINGS['controlling']]
	
	_situation = {}
	_situation['armed'] = alife.combat.has_potentially_usable_weapon(_life)
	_situation['friends'] = len([l for l in _life['know'].values() if l['alignment'] in ['trust', 'feign_trust']])
	_situation['group'] = _life['group']
	_situation['online_alife'] = [l for l in LIFE.values() if l['online'] and not l['dead'] and not l['id'] == _life['id']]
	_situation['trusted_online_alife'] = [l for l in _situation['online_alife'] if alife.judgement.can_trust(_life, l['id'])]
	_situation['has_radio'] = len(lfe.get_all_inventory_items(_life, matches=[{'type': 'radio'}]))>0
	
	return _situation

def get_group_leader_with_motive(group_motive, online=False):
	for life in LIFE.values():
		if not (life['online'] or not online) or not life['group'] or not alife.groups.is_leader(life, life['group'], life['id']) or SETTINGS['controlling'] == life['id']:
			continue
		
		if alife.groups.get_motive(life, life['group']) == group_motive:
			return life['id']
	
	return None

def spawn_life(life_type, position, event_time, **kwargs):
	_life = {'type': life_type, 'position': position[:]}
	_life.update(**kwargs)
	         
	WORLD_INFO['scheme'].append({'life': _life, 'time': event_time})

def order_group(life, group_id, stage, event_time, **kwargs):
	WORLD_INFO['scheme'].append({'group': group_id, 'member': life['id'], 'stage': stage, 'flags': kwargs, 'time': WORLD_INFO['ticks']+event_time})

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

def get_overwatch_hardship():
	_stats = WORLD_INFO['overwatch']
	_situation = get_player_situation()
	
	if not _situation:
		return 0
	
	if _situation['online_alife'] == _situation['trusted_online_alife']:
		_mod = float(_stats['last_updated'])/float(WORLD_INFO['ticks'])
	else:
		_mod = 1
	
	_hardship = _stats['loss_experienced']
	_hardship += _stats['danger_experienced']
	_hardship += _stats['injury']
	_hardship += _stats['human_encounters']*2
	_hardship *= _mod
	
	return _hardship

def evaluate_overwatch_mood():
	_stats = WORLD_INFO['overwatch']
	_hardship = get_overwatch_hardship()
	
	#print _hardship, _mod, _stats['rest_level'], (_stats['last_updated']/float(WORLD_INFO['ticks']))
	
	_success = 0
	
	#if _stats['mood'] == 'rest':
	#	if _mod > _stats['rest_level']:
	#		return False
	#	
	#	_stats['mood'] = random.choice(['rest', 'hurt'])
	#elif _stats['mood'] == 'hurt':
	if _hardship-_success >= 3:
		_stats['mood'] = 'rest'
	else:
		_stats['mood'] = 'hurt'

def record_encounter(amount, life_ids=None):
	WORLD_INFO['overwatch']['human_encounters'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	if life_ids:
		WORLD_INFO['overwatch']['tracked_alife'].extend(life_ids)
	
	logging.debug('[Overwatch] encounter (%s)' % amount)

def record_dangerous_event(amount):
	WORLD_INFO['overwatch']['danger_experienced'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	logging.debug('[Overwatch] Danger (%s)' % amount)

def record_loss(amount):
	WORLD_INFO['overwatch']['loss_experienced'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	logging.debug('[Overwatch] Loss (%s)' % amount)

def record_injury(amount):
	WORLD_INFO['overwatch']['injury'] += amount
	WORLD_INFO['overwatch']['last_updated'] = WORLD_INFO['ticks']
	
	logging.debug('[Overwatch] injury (%s)' % amount)

def create_intro_story():
	_i = 2#random.randint(0, 2)
	_player = LIFE[SETTINGS['controlling']]
	
	WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']
	
	if _i == 1:
		#broadcast([{'text': 'You wake up from a deep sleep.'},
		#           {'text': 'You don\'t remember anything.', 'change_only': True}], 0, glitch=True)
		
		_spawn_items = ['leather backpack', 'M9', '9x19mm magazine']
		
		for i in range(14):
			_spawn_items.append('9x19mm round')
		
		for item_name in _spawn_items:
			lfe.add_item_to_inventory(_player, items.create_item(item_name))
		
		lfe.set_pos(_player, spawns.get_spawn_in_ref('farms'))
		
		#Dead dude
		_dead_guy = lfe.create_life('human', position=spawns.get_spawn_point_around(_player['pos']))
		_dead_guy['dead'] = True
		
		if _player['pos'] == _dead_guy['pos']:
			lfe.set_pos(_dead_guy, [_dead_guy['pos'][0], _dead_guy['pos'][1], _dead_guy['pos'][2]+1])
		
		for i in range(random.randint(15, 20)):
			effects.create_splatter('blood', spawns.get_spawn_point_around(_dead_guy['pos'], area=2), intensity=8)
		
		#Group nearby
		_bandit_group_spawn_chunk = alife.chunks.get_chunk_key_at(spawns.get_spawn_point_around(_player['pos'], min_area=60, area=90))
		_bandit_group = spawns.generate_group('bandit', amount=3, spawn_chunks=[_bandit_group_spawn_chunk])
		
		_friendly_group_spawn_chunk = alife.chunks.get_chunk_key_at(spawns.get_spawn_point_around(_player['pos'], min_area=10, area=20))
		_friendly_group = spawns.generate_group('loner_riflemen', amount=2, spawn_chunks=[_friendly_group_spawn_chunk])
		
		for ai in _bandit_group:
			_target = alife.brain.meet_alife(ai, _player)
			_target['last_seen_time'] = 1
			_target['escaped'] = 1
			_target['last_seen_at'] = _player['pos'][:]
			
			alife.stats.establish_hostile(ai, _player['id'])
			alife.stats.establish_hostile(_player, ai['id'])
			
			for target in _friendly_group:
				_target = alife.brain.meet_alife(ai, target)
				_target['last_seen_time'] = 1
				_target['escaped'] = 1
				_target['last_seen_at'] = target['pos'][:]
				alife.stats.establish_hostile(ai, target['id'])
				
				_group_target = alife.brain.meet_alife(target, ai)
				_group_target['last_seen_time'] = 1
				_group_target['escaped'] = 1
				_group_target['last_seen_at'] = ai['pos'][:]
				alife.stats.establish_hostile(target, ai['id'])
		
		#Wounded running away
		_wounded_guy = _friendly_group[0]
		
		if _wounded_guy['pos'] == _dead_guy['pos']:
			_wounded_guy['pos'][0] -= 1
		
		alife.brain.meet_alife(_wounded_guy, _player)['alignment'] = 'trust'
		alife.brain.meet_alife(_player, _wounded_guy)['alignment'] = 'trust'
		
		#alife.speech.start_dialog(_wounded_guy, _player['id'], 'incoming_targets', force=True)
		alife.memory.create_question(_wounded_guy, _player['id'], 'incoming_targets')
		alife.memory.create_question(_wounded_guy, _player['id'], 'incoming_targets_follow', group_id=_wounded_guy['group'])
	
	elif _i == 2:
		lfe.set_pos(_player, spawns.get_spawn_in_ref('farms'))

def form_scheme(force=False):
	if (WORLD_INFO['scheme'] or (WORLD_INFO['ticks']-WORLD_INFO['last_scheme_time'])<200) and not force:
		return False
	
	_overwatch_mood = WORLD_INFO['overwatch']['mood']
	
	if _overwatch_mood == 'rest':
		return False
	
	_player_situation = get_player_situation()
	
	if _overwatch_mood == 'hurt':
		if hurt_player(_player_situation):
			WORLD_INFO['last_scheme_time'] = WORLD_INFO['ticks']
			
			return True
	
	#if _player_situation['armed']:
	_i = random.randint(0, 3)+10
	
	if _i == 1:
		_military_group_leader = get_group_leader_with_motive('military')
		_bandit_group_leader = get_group_leader_with_motive('crime', online=False)
		
		#TODO: Actual bandit camp location
		if _military_group_leader and _bandit_group_leader:
			_bandit_group_location = lfe.get_current_chunk_id(LIFE[_bandit_group_leader])
			order_group(LIFE[_military_group_leader], LIFE[_military_group_leader]['group'], STAGE_RAIDING, 30, chunk_key=_bandit_group_location)
			alife.groups.discover_group(LIFE[_military_group_leader], LIFE[_bandit_group_leader]['group'])
			alife.groups.declare_group_hostile(LIFE[_military_group_leader], LIFE[_military_group_leader]['group'], LIFE[_bandit_group_leader]['group'])
	
	elif _i == 2:
		_spawn_pos = spawns.get_spawn_in_ref('farms')
		_real_direction = language.get_real_direction(numbers.direction_to((MAP_SIZE[0]/2, MAP_SIZE[1]/2), _spawn_pos))
		
		spawn_life('loner', _spawn_pos, 35, injuries={'llowerleg': {'cut': 1}})

		_messages = [{'text': 'Hello? Can anyone hear me?'},
	                 {'text': 'Bandits robbed me and left me to bleed out...'},
	                 {'text': 'I\'m by a farm to the %s.' % _real_direction},
	                 {'text': 'They might still be around. Please hurry!'}]
		broadcast(_messages, 40)
	
	elif 1 == 1:
		_bandit_group_leader = get_group_leader_with_motive('crime', online=True)
		_military_group_leader = get_group_leader_with_motive('military', online=False)
		
		if _military_group_leader and _bandit_group_leader:
			_bandit_group_location = lfe.get_current_chunk_id(LIFE[_bandit_group_leader])
			_military_group_location = lfe.get_current_chunk_id(LIFE[_military_group_leader])
			order_group(LIFE[_bandit_group_leader], LIFE[_bandit_group_leader]['group'], STAGE_RAIDING, 500, chunk_key=_military_group_location)
			alife.groups.discover_group(LIFE[_bandit_group_leader], LIFE[_military_group_leader]['group'])
			alife.groups.declare_group_hostile(LIFE[_bandit_group_leader], LIFE[_bandit_group_leader]['group'], LIFE[_military_group_leader]['group'])

			_real_direction = language.get_real_direction(numbers.direction_to((MAP_SIZE[0]/2, MAP_SIZE[1]/2), alife.chunks.get_chunk(_military_group_location)['pos']))
		
			_messages = [{'text': 'Attention all neutral and bandit squads.'},
				         {'text': 'We finally got solid contact on military in the %s compound.' % _real_direction},
				         {'text': 'We\'re located near coords %s and heading out soon.' % (', '.join(_bandit_group_location.split(',')))}]
			broadcast(_messages, 40)
		
	#if not WORLD_INFO['scheme'] and WORLD_INFO['ticks'] < 100:
		#if 1==1:#random.randint(0, 5):
			
		#else: #TODO: Get group
		#	_bandit_raid_direction = 'north'
		#	
		#	_messages = [{'text': 'This is %s of %s, broadcasting to all.', 'source': 'Group Leader'},
		#                 {'text': 'We\'re in dire need of help near <location>.', 'source': 'Group Leader'},
		#                 {'text': 'A group of bandits is approaching from the %s.' % _bandit_raid_direction, 'source': 'Group Leader'},
		#                 {'text': 'If you are able to fight, please! We need fighters!', 'source': 'Group Leader'}]
		#	broadcast(_messages, 40)

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
	
	_situation = get_player_situation()
	
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

def hurt_player(situation):
	if not SETTINGS['controlling']:
		return False
	
	_player = LIFE[SETTINGS['controlling']]
	
	if situation['group']:
		if situation['armed']:
			_bandit_group_leader = get_group_leader_with_motive('crime', online=True)
			_military_group_leader = get_group_leader_with_motive('military', online=False)
			
			if not _military_group_leader:
				_military_group_leader = spawns.generate_group('soldier', amount=3, spawn_chunks=[spawns.get_spawn_in_ref('outposts', chunk_key=True)])[0]
			
			if not _bandit_group_leader:
				_chunk_key = alife.chunks.get_chunk_key_at(spawns.get_spawn_point_around(_military_group_leader['pos'], area=150, min_area=100))
				_bandit_group_leader = spawns.generate_group('bandit', amount=5, spawn_chunks=[_chunk_key])[0]
			
			_bandit_group_location = lfe.get_current_chunk_id(_bandit_group_leader)
			_military_group_location = lfe.get_current_chunk_id(_military_group_leader)
			order_group(_bandit_group_leader, _bandit_group_leader['group'], STAGE_RAIDING, 500, chunk_key=_military_group_location)
			alife.groups.discover_group(_bandit_group_leader, _military_group_leader['group'])
			alife.groups.declare_group_hostile(_bandit_group_leader, _bandit_group_leader['group'], _military_group_leader['group'])

			_real_direction = language.get_real_direction(numbers.direction_to((MAP_SIZE[0]/2, MAP_SIZE[1]/2), alife.chunks.get_chunk(_military_group_location)['pos']))
		
			_messages = [{'text': 'Attention all neutral and bandit squads.'},
		                 {'text': 'We finally got solid contact on military in the %s compound.' % _real_direction},
		                 {'text': 'We\'re located near coords %s and heading out soon.' % (', '.join(_bandit_group_location.split(',')))}]
			broadcast(_messages, 40)
			record_encounter(len(alife.groups.get_group(_military_group_leader, _military_group_leader['group'])['members']))
			
			_player_group_leader = LIFE[alife.groups.get_leader(_player, situation['group'])]
			
			for friendly_member in alife.groups.get_group(_player_group_leader, situation['group'])['members']:
				for hostile_member in alife.groups.get_group(_military_group_leader, _military_group_leader['group'])['members']:
					_target = alife.brain.meet_alife(LIFE[friendly_member], LIFE[hostile_member])
					_target['last_seen_time'] = 1
					_target['escaped'] = 1
					_target['last_seen_at'] = LIFE[hostile_member]['pos'][:]
					alife.stats.establish_hostile(LIFE[friendly_member], hostile_member)
			
			for hostile_member in alife.groups.get_group(_military_group_leader, _military_group_leader['group'])['members']:		
				for friendly_member in alife.groups.get_group(_player_group_leader, situation['group'])['members']:
					_target = alife.brain.meet_alife(LIFE[hostile_member], LIFE[friendly_member])
					_target['last_seen_time'] = 1
					_target['escaped'] = 1
					_target['last_seen_at'] = LIFE[friendly_member]['pos'][:]
					alife.stats.establish_hostile(LIFE[hostile_member], friendly_member)
			
			return True
	else:
		_town_chunk_keys = []
		for ref in WORLD_INFO['refs']['towns']:
			_town_chunk_keys.extend(ref)
		
		_nearest_town_chunk_key = alife.chunks.get_nearest_chunk_in_list(_player['pos'], _town_chunk_keys)
		_town_chunk = alife.chunks.get_chunk(_nearest_town_chunk_key)
		_distance_to_nearst_town = numbers.distance(_player['pos'], _town_chunk['pos'])
		_spawn_distance = 15*WORLD_INFO['chunk_size']
		
		if len(situation['online_alife']) == len(situation['trusted_online_alife']):
			if _distance_to_nearst_town<=50:
				_group_spawn_velocity = numbers.velocity(numbers.direction_to(_player['pos'], _town_chunk['pos']), _spawn_distance+(50-numbers.clip(_distance_to_nearst_town, 0, 50)))
				_group_spawn_pos = [int(round(_player['pos'][0]+_group_spawn_velocity[0])), int(round(_player['pos'][1]+_group_spawn_velocity[1]))]
				_group_spawn_pos[0] = numbers.clip(_group_spawn_pos[0], 0, MAP_SIZE[0])
				_group_spawn_pos[1] = numbers.clip(_group_spawn_pos[1], 0, MAP_SIZE[1])
				_group_spawn_chunk_key = alife.chunks.get_chunk_key_at(spawns.get_spawn_point_around(_group_spawn_pos, area=30))
				
				_alife = spawns.generate_group('bandit', amount=2, spawn_chunks=[_group_spawn_chunk_key])
				
				for ai in _alife:
					alife.brain.meet_alife(ai, _player)
					alife.stats.establish_hostile(ai, _player['id'])
				
				record_encounter(2, life_ids=[i['id'] for i in _alife])
			
				if random.randint(0, 1) or 1:
					_spawn_chunk_key = spawns.get_spawn_point_around(_group_spawn_pos, area=90, min_area=60, chunk_key=True)
					_other_group = spawns.generate_group('loner', amount=1, spawn_chunks=[_spawn_chunk_key])
					
					for ai in _other_group:
						for ai2 in _alife:
							_target = alife.brain.meet_alife(ai, ai2)
							_target['last_seen_time'] = 1
							_target['escaped'] = 1
							_target['last_seen_at'] = ai2['pos'][:]
							
							alife.stats.establish_hostile(ai, ai2['id'])
					
					for ai2 in _alife:
						for ai in _other_group:
							_target = alife.brain.meet_alife(ai2, ai)
							_target['last_seen_time'] = 1
							_target['escaped'] = 1
							_target['last_seen_at'] = ai['pos'][:]
							
							alife.stats.establish_hostile(ai2, ai['id'])
					
					_messages = [{'text': 'I\'m pinned down in the village!'},
					             {'text': 'Anyone nearby?'}]
					broadcast(_messages, 0)
				
				return True
			
	return False
