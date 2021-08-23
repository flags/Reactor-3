from globals import *

import life as lfe

from . import judgement
from . import movement
import weapons
from . import speech
import melee
import zones
import items
from . import sight
from . import stats
from . import brain
from . import jobs

import bad_numbers
import logging
import random


def get_engage_distance(life):
	_weapons = get_equipped_weapons(life)
	
	if _weapons:
		return bad_numbers.clip(int(round(ITEMS[_weapons[0]]['accuracy']*29)), 3, sight.get_vision(life))
	else:
		return sight.get_vision(life)//2

def weapon_is_working(life, item_uid):
	_weapon = ITEMS[item_uid]
	_feed_uid = weapons.get_feed(_weapon)
	
	if _feed_uid and ITEMS[_feed_uid]['rounds']:
		return True
	
	return False

def weapon_equipped_and_ready(life):
	if not is_any_weapon_equipped(life):
		return False
	
	_loaded_feed = None
	for weapon in get_equipped_weapons(life):
		if weapon_is_working(life, weapon):
			return True
	
	return False

def weapon_is_in_preferred_working_condition(life, item_uid):
	return len(get_all_ammo_for_weapon(life, item_uid))>=5

def get_target_positions_and_zones(life, targets, ignore_escaped=False):
	_target_positions = []
	_zones = []
	
	for _target in targets:
		_known_target = brain.knows_alife_by_id(life, _target)
		
		if ignore_escaped and _known_target['escaped'] or not _known_target['last_seen_at']:
			continue
		
		_target_positions.append(_known_target['last_seen_at'])
		_zone = zones.get_zone_at_coords(_known_target['last_seen_at'])
		
		if not _zone in _zones:
			_zones.append(_zone)
	
	_zone = zones.get_zone_at_coords(life['pos'])
	
	if not _zone in _zones:
		_zones.append(_zone)
		
	return _target_positions, _zones

def reload_weapon(life, weapon_uid):
	_weapon = ITEMS[weapon_uid]
	_feed = _get_feed(life, _weapon)
	
	if not _feed:
		logging.error('No feed for weapon, but trying to reload anyway.')
		
		return False
	
	_refill = _refill_feed(life, _feed)
	
	if _refill:
		load_feed(life, weapon_uid, _feed['uid'])
	
	return weapons.get_feed(_weapon)

def load_feed(life, weapon_uid, feed_uid):
	_load_action = {'action': 'reload',
	                'weapon': ITEMS[weapon_uid],
	                'ammo': ITEMS[feed_uid]}
	
	if lfe.find_action(life, matches=[_load_action]):
		return False
	
	lfe.add_action(life, _load_action, 200, delay=0)
	
	return True

def _get_feed(life, weapon):
	_feeds = lfe.get_all_inventory_items(life, matches=[{'type': weapon['feed'], 'ammotype': weapon['ammotype']}], ignore_actions=False)

	_highest_feed = {'rounds': [], 'feed': None}
	for feed in [lfe.get_inventory_item(life, _feed['uid']) for _feed in _feeds]:
		if len(feed['rounds']) > len(_highest_feed['rounds']):
			_highest_feed['rounds'] = feed['rounds']
			_highest_feed['feed'] = feed
	
	return _highest_feed['feed']

def _refill_feed(life, feed):
	if not lfe.is_holding(life, feed['uid']) and not lfe.can_hold_item(life):
		logging.warning('No hands free to load ammo!')
		
		return False

	if not lfe.get_held_items(life, matches=[{'id': feed['uid']}]) and lfe.item_is_stored(life, feed['uid']) and not lfe.find_action(life, matches=[{'action': 'removeandholditem'}]):
		lfe.add_action(life,{'action': 'removeandholditem',
			'item': feed['uid']},
			200,
			delay=0)
		
		return False

	#TODO: No check for ammo type.
	
	_loading_rounds = len(lfe.find_action(life, matches=[{'action': 'refillammo'}]))
	_bullets_in_inventory = len(lfe.get_all_inventory_items(life, matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}]))
	
	if _loading_rounds:# >= _bullets_in_inventory:
		return False
	
	if len(lfe.find_action(life,matches=[{'action': 'refillammo'}])):
		return False
	
	_rounds = len(feed['rounds'])
	
	if _rounds>=feed['maxrounds'] or (not _bullets_in_inventory and _rounds):
		print('Full?')
		return True
	
	_ammo_count = len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}]))
	_ammo_count += len(feed['rounds'])
	_rounds_to_load = bad_numbers.clip(_ammo_count,0,feed['maxrounds'])
	for ammo in lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}])[:_rounds_to_load]:		
		lfe.add_action(life,{'action': 'refillammo',
			'ammo': feed,
			'round': ammo},
			200,
			delay=3)
		
		_rounds += 1
	
	return False

def _equip_weapon(life, weapon_uid, feed_uid):
	_weapon = ITEMS[weapon_uid]
	_feed = ITEMS[feed_uid]
	
	#TODO: Need to refill ammo?
	if not weapons.get_feed(_weapon):
		#TODO: How much time should we spend loading rounds if we're in danger?
		
		if _refill_feed(life, _feed):
			load_feed(life, _weapon['uid'], _feed['uid'])
	else:
		print('should be equippan?')
		lfe.add_action(life,{'action': 'equipitem',
			'item': weapon_uid},
			300,
			delay=0)
		
		print('Loaded!')
		return True
	
	return True

def is_any_weapon_equipped(life):
	if lfe.get_held_items(life, matches=[{'type': 'gun'}]):
		return True
	
	return False

def prepare_for_ranged(life):
	if weapon_equipped_and_ready(life):
		return True
	
	return False

def get_equipped_weapons(life):
	return lfe.get_held_items(life, matches=[{'type': 'gun'}])

def get_weapons(life):
	return lfe.get_all_inventory_items(life, matches=[{'type': 'gun'}], ignore_actions=False)

def get_loose_ammo_for_weapon(life, weapon_uid):
	_weapon = ITEMS[weapon_uid]
	
	return lfe.get_all_inventory_items(life, matches=[{'type': 'bullet', 'ammotype': _weapon['ammotype']}], ignore_actions=True)

def get_all_ammo_for_weapon(life, weapon_uid):
	_ammo = get_loose_ammo_for_weapon(life, weapon_uid)
	
	for feed in get_feeds_for_weapon(life, weapon_uid):
		_ammo.extend([ITEMS[r] for r in feed['rounds']])
	
	return _ammo

def get_feeds_for_weapon(life, weapon_uid):
	_weapon = ITEMS[weapon_uid]
	
	return lfe.get_all_inventory_items(life, matches=[{'type': _weapon['feed'], 'ammotype': _weapon['ammotype']}], ignore_actions=True)

def have_feed_and_ammo_for_weapon(life, weapon_uid):
	_weapon = ITEMS[weapon_uid]
	
	_feed = get_feeds_for_weapon(life, weapon_uid)
	_ammo = get_all_ammo_for_weapon(life, weapon_uid)
	
	if _feed and _ammo:
		return True
	
	return False

def has_potentially_usable_weapon(life):
	for weapon in get_weapons(life):
		if get_feeds_for_weapon(life, weapon['uid']):
			if len(get_all_ammo_for_weapon(life, weapon['uid'])):
				return True
		
		if weapon_is_working(life, weapon['uid']):
			return True
	
	return False

def has_ready_weapon(life):
	for weapon in get_weapons(life):
		if weapon_is_working(life, weapon['uid']):
			return weapon
	
	return False

def get_best_weapon(life):
	_weapons = lfe.get_all_inventory_items(life, matches=[{'type': 'gun'}], ignore_actions=True)
	
	_best_wep = {'weapon': None, 'feed': None, 'rounds': 0}
	for _wep in _weapons:
		_feed_rounds = 0
		_free_rounds = 0
		_feeds = lfe.get_all_inventory_items(life,
			matches=[{'type': _wep['feed'],'ammotype': _wep['ammotype']}])
		
		_loaded_feed_uid = weapons.get_feed(_wep)
		if _loaded_feed_uid:
			_loaded_feed = items.get_item_from_uid(_loaded_feed_uid)
			
			if len(_loaded_feed['rounds'])>_best_wep['rounds']:
				_best_wep['weapon'] = _wep
				_best_wep['feed'] = _loaded_feed
				_best_wep['rounds'] = len(_loaded_feed['rounds'])
				continue

		for _feed in _feeds:
			_feed_rounds = len(_feed['rounds'])
			_free_rounds = len(lfe.get_all_inventory_items(life,
				matches=[{'type': 'bullet', 'ammotype': _wep['ammotype']}]))
			
			if _feed_rounds+_free_rounds > _best_wep['rounds']:
				_best_wep['weapon'] = _wep
				_best_wep['feed'] = _feed
				_best_wep['rounds'] = _feed_rounds+_free_rounds
	
	if not _best_wep['weapon'] or not _best_wep['feed']:
		return False
	
	return _best_wep

def get_exposed_positions(life):
	_cover_exposed_at = brain.get_flag(life, 'cover_exposed_at')
	
	if _cover_exposed_at:
		return _cover_exposed_at
	
	return []

def get_closest_target(life, targets):
	if targets:
		_target_positions, _zones = get_target_positions_and_zones(life, targets)
	else:
		return False
	
	_closest_target = {'target_id': None, 'score': 9999}
	for t in [brain.knows_alife_by_id(life, t_id) for t_id in targets]:
		_distance = bad_numbers.distance(life['pos'], t['last_seen_at'])
		
		if _distance < _closest_target['score']:
			_closest_target['score'] = _distance
			_closest_target['target_id'] = t['life']['id']
	
	return _closest_target['target_id']

def ranged_combat(life, targets):
	_target = brain.knows_alife_by_id(life, get_closest_target(life, targets))
	
	#if not _target:
	#	for target_id in targets:
	#		if brain.knows_alife_by_id(life, target_id)['escaped']:
	#			continue
	#		
	#		brain.knows_alife_by_id(life, target_id)['escaped'] = 1
	#	
	#	logging.error('No target for ranged combat.')
	#	
	#	return False
	
	_engage_distance = get_engage_distance(life)
	_path_dest = lfe.path_dest(life)
	
	if not _path_dest:
		_path_dest = life['pos'][:]
	
	_target_distance = bad_numbers.distance(life['pos'], _target['last_seen_at'])
	
	#Get us near the target
	#if _target['last_seen_at']:
	movement.position_to_attack(life, _target['life']['id'], _engage_distance)
		
	if sight.can_see_position(life, _target['last_seen_at']):
		if _target_distance	<= _engage_distance:
			if sight.can_see_position(life, _target['life']['pos']):
				if not sight.view_blocked_by_life(life, _target['life']['pos'], allow=[_target['life']['id']]):
					lfe.clear_actions(life)
					
					if not len(lfe.find_action(life, matches=[{'action': 'shoot'}])) and _target['time_visible']>2:
						for i in range(weapons.get_rounds_to_fire(weapons.get_weapon_to_fire(life))):
							lfe.add_action(life, {'action': 'shoot',
							                      'target': _target['last_seen_at'],
							                      'target_id': _target['life']['id'],
							                      'limb': 'chest'},
							               300,
							               delay=int(round(life['recoil']-stats.get_recoil_recovery_rate(life))))
				else:
					_friendly_positions, _friendly_zones = get_target_positions_and_zones(life, judgement.get_trusted(life))
					_friendly_zones.append(zones.get_zone_at_coords(life['pos']))
					_friendly_positions.append(life['pos'][:])
					
					if not lfe.find_action(life, [{'action': 'dijkstra_move', 'orig_goals': [_target['life']['pos'][:]], 'avoid_positions': _friendly_positions}]):
						lfe.add_action(life, {'action': 'dijkstra_move',
						                      'rolldown': True,
						                      'zones': _friendly_zones,
						                      'goals': [_target['life']['pos'][:]],
						                      'orig_goals': [_target['life']['pos'][:]],
						                      'avoid_positions': _friendly_positions,
						                      'reason': 'combat_position'},
						               100)
			else:
				lfe.memory(life,'lost sight of %s' % (' '.join(_target['life']['name'])), target=_target['life']['id'])
				
				_target['escaped'] = 1
				
				for send_to in judgement.get_trusted(life):
					speech.communicate(life,
					                   'target_missing',
					                   target=_target['life']['id'],
					                   matches=[send_to])
		#else:
			#print life['name']
			#_friendly_positions, _friendly_zones = get_target_positions_and_zones(life, judgement.get_trusted(life))
			#_friendly_zones.append(zones.get_zone_at_coords(life['pos']))
			#_friendly_positions.append(life['pos'][:])
			
			#if not lfe.find_action(life, [{'action': 'dijkstra_move', 'orig_goals': [_target['life']['pos'][:]], 'avoid_positions': _friendly_positions}]):
			#	lfe.add_action(life, {'action': 'dijkstra_move',
			#		                'rolldown': True,
			#		                'zones': _friendly_zones,
			#		                'goals': [_target['life']['pos'][:]],
			#		                'orig_goals': [_target['life']['pos'][:]],
			#		                'avoid_positions': _friendly_positions,
			#		                'reason': 'combat_position'},
			#		         100)
			#	
			#	print '2'
		
	else:
		return False

def melee_combat(life, targets):
	_target = get_closest_target(life, targets)
	
	if not _target:
		logging.error('No target for melee combat.')
		return False
	
	if sight.can_see_position(life, _target['last_seen_at'], block_check=True, strict=True):
		_can_see = sight.can_see_position(life, _target['life']['pos'], get_path=True)
		
		if _can_see:
			if len(_can_see)>1:
				movement.find_target(life, _target['life']['id'], distance=1, follow=True)
			else:
				melee.fight(life, _target['life']['id'])
		else:
			lfe.memory(life,'lost sight of %s' % (' '.join(_target['life']['name'])), target=_target['life']['id'])
			
			_target['escaped'] = 1
			
			for send_to in judgement.get_trusted(life):
				speech.communicate(life,
			        'target_missing',
			        target=_target['life']['id'],
			        matches=[send_to])
	else:
		return False