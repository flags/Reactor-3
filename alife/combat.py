from globals import *

import life as lfe

import judgement
import movement
import weapons
import speech
import zones
import items
import sight
import stats
import brain
import jobs

import numbers
import logging
import random

def weapon_equipped_and_ready(life):
	if not is_any_weapon_equipped(life):
		return False
	
	_loaded_feed = None
	for weapon in get_equipped_weapons(life):
		_feed_uid = weapons.get_feed(weapon)
		
		if _feed_uid and items.get_item_from_uid(_feed_uid)['rounds']:
			_loaded_feed = True #items.get_item_from_uid(_feed_uid)

	if not _loaded_feed:
		#logging.warning('%s has feed with no ammo!' % (' '.join(life['name'])))
		return False
	
	return True

def get_target_positions_and_zones(life, targets, ignore_escaped=False):
	_target_positions = []
	_zones = []
	
	for _target in targets:
		_known_target = brain.knows_alife_by_id(life, _target)
		
		if ignore_escaped and _known_target['escaped']:
			continue
		
		_target_positions.append(_known_target['last_seen_at'])
		_zone = zones.get_zone_at_coords(_known_target['last_seen_at'])
		
		if not _zone in _zones:
			_zones.append(_zone)
	
	_zone = zones.get_zone_at_coords(life['pos'])
	
	if not _zone in _zones:
		_zones.append(_zone)
		
	return _target_positions, _zones

def _get_feed(life, weapon):
	_feeds = lfe.get_all_inventory_items(life,matches=[{'type': weapon['feed'],'ammotype': weapon['ammotype']}])

	_highest_feed = {'rounds': -1,'feed': None}
	for feed in [lfe.get_inventory_item(life,_feed['uid']) for _feed in _feeds]:
		if feed['rounds']>_highest_feed['rounds']:
			_highest_feed['rounds'] = feed['rounds']
			_highest_feed['feed'] = feed
	
	return _highest_feed['feed']

def _refill_feed(life,feed):
	if not lfe.is_holding(life, feed['uid']) and not lfe.can_hold_item(life):
		logging.warning('No hands free to load ammo!')
		
		return False
	
	#TODO: Actual programming
	if not lfe.get_held_items(life,matches=[{'id': feed['uid']}]) and (lfe.item_is_stored(life, feed['uid']) or feed['uid'] in life['inventory']) and lfe.find_action(life, matches=[{'action': 'removeandholditem'}]):
		_hold = lfe.add_action(life,{'action': 'removeandholditem',
			'item': feed['uid']},
			200,
			delay=0)

	#TODO: No check for ammo type.
	
	_loading_rounds = len(lfe.find_action(life,matches=[{'action': 'refillammo'}]))
	if _loading_rounds >= len(lfe.get_all_inventory_items(life,matches=[{'type': 'bullet', 'ammotype': feed['ammotype']}])):
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

def _equip_weapon(life, weapon, feed):
	#TODO: Need to refill ammo?
	if not weapons.get_feed(weapon):
		#TODO: How much time should we spend loading rounds if we're in danger?
		if _refill_feed(life, feed):
			lfe.add_action(life,{'action': 'reload',
		          'weapon': weapon,
		          'ammo': feed},
		          200,
		          delay=0)
	else:
		print 'should be equippan?'
		lfe.add_action(life,{'action': 'equipitem',
			'item': weapon['uid']},
			300,
			delay=0)
		
		print 'Loaded!'
		return True
	
	return True

def is_any_weapon_equipped(life):
	_weapon = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	
	if _weapon:
		return True
	
	return False

def prepare_for_ranged(life):
	if weapon_equipped_and_ready(life):
		return True
	else:
		if not 'equipping' in life:
			if combat._equip_weapon(life):
				life['equipping'] = True

def get_equipped_weapons(life):
	return [lfe.get_inventory_item(life, _wep) for _wep in lfe.get_held_items(life,matches=[{'type': 'gun'}])]

def has_weapon(life):
	return lfe.get_all_inventory_items(life,matches=[{'type': 'gun'}])

def has_usable_weapon(life):
	for weapon in lfe.get_all_inventory_items(life,matches=[{'type': 'gun'}]):
		if lfe.get_all_inventory_items(life, matches=[{'type': weapon['feed'],'ammotype': weapon['ammotype']}]):
			return True
	
	return False

def get_best_weapon(life):
	_weapons = lfe.get_all_inventory_items(life,matches=[{'type': 'gun'}])
	
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

def melee_combat(life, target):
	_target = brain.knows_alife_by_id(life, target)
	
	if numbers.distance(life['pos'], _target['last_seen_at']) > 1:
		movement.travel_to_position(life, _target['last_seen_at'])
	elif sight.can_see_position(life, _target['life']['pos']):
		lfe.clear_actions(life, matches=[{'action': 'move'}])
		
		lfe.add_action(life,{'action': 'bite',
			'target': _target['life']['id'],
			'limb': random.choice(_target['life']['body'].keys())},
			5000,
			delay=0)
	else:
		_target['escaped'] = 1

def ranged_combat(life, target):
	target = brain.knows_alife_by_id(life, target)
	_pos_for_combat = movement.position_for_combat(life, [target['life']['id']], target['last_seen_at'], WORLD_INFO['map'])
	print _pos_for_combat
	
	if not target['escaped'] and not _pos_for_combat:
		if life['path']:
			return False
		else:
			return movement.escape(life, [target['life']['id']])
			
	elif _pos_for_combat:
		lfe.stop(life)
	
	if not sight.can_see_position(life,target['life']['pos']):
		if not movement.travel_to_position(life, target['last_seen_at'], stop_on_sight=True):
			lfe.memory(life,'lost sight of %s' % (' '.join(target['life']['name'])),target=target['life']['id'])
			
			for send_to in judgement.get_trusted(life):
				speech.communicate(life,
					'target_missing',
					target=target['life']['id'],
					matches=[{'id': send_to}])
		else:
			if sight.can_see_position(life, target['last_seen_at']):
				target['escaped'] = 1
		
		return False
	
	#TODO: Attach skill to delay
	if not len(lfe.find_action(life,matches=[{'action': 'shoot'}])):
		lfe.add_action(life,{'action': 'shoot',
			'target': target['life']['pos'][:],
			'limb': 'chest'},
			5000,
			delay=int(round(life['recoil']/stats.get_recoil_recovery_rate(life))))

def needs_cover(life):
	if not lfe.execute_raw(life, 'safety', 'needs_cover'):
		return False
	
	_goals = []
	_zones = []
	for target in [brain.knows_alife_by_id(life, t) for t in judgement.get_targets(life)]:
		_goals.append(target['last_seen_at'])
		_zone = zones.get_zone_at_coords(target['last_seen_at'])
		
		if not _zone in _zones:
			_zones.append(_zone)
	
	_distance_to_danger = zones.dijkstra_map(life['pos'], _goals, _zones, return_score=True)
	print life['name'], _distance_to_danger
	#TODO: Un-hardcode
	if _distance_to_danger<10:
		print 'needs cover'*10
		return True
	
	return False