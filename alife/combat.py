from globals import *

import life as lfe

import judgement
import movement
import weapons
import speech
import melee
import zones
import items
import sight
import stats
import brain
import jobs

import numbers
import logging
import random

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
			_loaded_feed = True
			break

	if _loaded_feed:
		#logging.warning('%s has feed with no ammo!' % (' '.join(life['name'])))
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
	_feeds = lfe.get_all_inventory_items(life, matches=[{'type': weapon['feed'], 'ammotype': weapon['ammotype']}], ignore_actions=True)

	_highest_feed = {'rounds': -1, 'feed': None}
	for feed in [lfe.get_inventory_item(life, _feed['uid']) for _feed in _feeds]:
		if feed['rounds']>_highest_feed['rounds']:
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
	
	_loading_rounds = len(lfe.find_action(life,matches=[{'action': 'refillammo'}]))
	if _loading_rounds >= len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}])):
		#TODO: What?
		if not _loading_rounds:
			return True
		
		return False
	
	if len(lfe.find_action(life,matches=[{'action': 'refillammo'}])):
		return False
	
	_rounds = len(feed['rounds'])
	
	if _rounds>=feed['maxrounds']:
		print 'Full?'
		return True
	
	_ammo_count = len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}]))
	_ammo_count += len(feed['rounds'])
	_rounds_to_load = numbers.clip(_ammo_count,0,feed['maxrounds'])
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
		print 'should be equippan?'
		lfe.add_action(life,{'action': 'equipitem',
			'item': weapon_uid},
			300,
			delay=0)
		
		print 'Loaded!'
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
	return lfe.get_all_inventory_items(life, matches=[{'type': 'gun'}], ignore_actions=True)

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
			if len(get_all_ammo_for_weapon(life, weapon['uid']))>=5:
				return True
		
		if weapon_is_working(life, weapon['uid']):
			return True
		
		#if not have_feed_and_ammo_for_weapon(life, weapon['uid']):
		#	continue
	
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
		#TODO: Dude, what?
		movement.find_target(life, targets, call=False)
		return False
	
	_targets_too_far = []
	_closest_target = {'target_id': None, 'score': 9999}
	for t in [brain.knows_alife_by_id(life, t_id) for t_id in targets]:
		_distance = numbers.distance(life['pos'], t['last_seen_at'])
		
		#NOTE: Hardcoding this for optimization reasons.
		if _distance>=100:
			targets.remove(t['life']['id'])
			_targets_too_far.append(t['life']['id'])
		
		if _distance < _closest_target['score']:
			_closest_target['score'] = _distance
			_closest_target['target_id'] = t['life']['id']
	
	if not _targets_too_far:
		_path_to_nearest = zones.dijkstra_map(life['pos'], _target_positions, _zones)
		
		if not _path_to_nearest:
			_path_to_nearest = [life['pos'][:]]
		
		if not _path_to_nearest:
			logging.error('%s lost known/visible target.' % ' '.join(life['name']))
			
			return False
		
		_target_pos = list(_path_to_nearest[len(_path_to_nearest)-1])
		#else:
		#	_target_pos = life['pos'][:]
		#	_target_positions.append(_target_pos)
		
		target = None
		
		if _target_pos in _target_positions:
			for _target in [brain.knows_alife_by_id(life, t) for t in targets]:
				if _target_pos == _target['last_seen_at']:
					target = _target
					break
	else:
		print 'THIS IS MUCH QUICKER!!!' * 10
		target = brain.knows_alife_by_id(life, _closest_target['target_id'])
	
	return target

def ranged_combat(life, targets):
	_target = get_closest_target(life, targets)
	
	if not _target:
		for target_id in targets:
			if brain.knows_alife_by_id(life, target_id)['escaped']:
				continue
			
			brain.knows_alife_by_id(life, target_id)['escaped'] = 1
		
		logging.error('No target for ranged combat.')
		return False
	
	if not life['path'] or not numbers.distance(lfe.path_dest(life), _target['last_seen_at']) == 0:
		movement.position_to_attack(life, _target['life']['id'])
	
	if sight.can_see_position(life, _target['last_seen_at'], block_check=True, strict=True) and not sight.view_blocked_by_life(life, _target['last_seen_at'], allow=[_target['life']['id']]):
		if sight.can_see_position(life, _target['life']['pos']):
			if not len(lfe.find_action(life, matches=[{'action': 'shoot'}])):
				for i in range(weapons.get_rounds_to_fire(weapons.get_weapon_to_fire(life))):
					lfe.add_action(life,{'action': 'shoot',
						'target': _target['last_seen_at'],
						'target_id': _target['life']['id'],
						'limb': 'chest'},
						5000,
						delay=int(round(life['recoil']-stats.get_recoil_recovery_rate(life))))
		else:
			lfe.memory(life,'lost sight of %s' % (' '.join(_target['life']['name'])), target=_target['life']['id'])
			
			_target['escaped'] = 1
			
			for send_to in judgement.get_trusted(life):
				speech.communicate(life,
			        'target_missing',
			        target=_target['life']['id'],
			        matches=[send_to])
	else:
		print life['name'], 'waiting...'
		return False

def melee_combat(life, targets):
	_target = get_closest_target(life, targets)
	
	if not _target:
		logging.error('No target for ranged combat.')
		return False
	
	if sight.can_see_position(life, _target['last_seen_at'], block_check=True, strict=True):
		_can_see = sight.can_see_position(life, _target['life']['pos'])
		
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
		print life['name'], 'waiting...'
		return False