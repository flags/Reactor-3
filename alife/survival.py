from globals import *
import life as lfe

import references
import judgement
import movement
import chunks
import speech

import logging
import numbers
import random
import combat
import items
import brain
import sight
import maps
import time

def create_need(life, need, need_callback, can_meet_callback, satisfy_callback, min_matches=1, cancel_if_flag=None):
	life['needs'].append({'need': need,
		'need_callback': need_callback,
	    'can_meet_callback': can_meet_callback,
	    'satisfy_callback': satisfy_callback,
		'min_matches': min_matches,
		'matches': [],
	    'can_meet_with': [],
	    'memory_location': None,
		'num_met': False,
	    'cancel_if_flag': cancel_if_flag})

def can_meet_need(life, need):
	_matches = []
	
	for meet_callback in need['can_meet_callback']:
		_matches.extend(meet_callback(life, matches=need['need']))
	
	need['can_meet_with'] = _matches
	
	return _matches

def is_need_active(life, need):
	if not need['cancel_if_flag']:
		return True
	
	if brain.get_flag(life, need['cancel_if_flag'][0]) == need['cancel_if_flag'][1]:
		return False
	
	return True

def is_in_need_matches(life, match):
	_matches = []
	
	for root_need in life['needs']:
		for item in root_need['matches']:
			_break = False

			for key in match:
				if not key in item or not item[key] == match[key]:
					_break = True
					break
			
			if _break:
				continue
			
			_matches.append(root_need)
	
	return _matches

def get_matched_needs(life, match):
	_matches = []
	
	for root_need in life['needs']:
		_break = False
		for need in root_need:
			for key in match:
				if not key in need or not need[key] == match[key]:
					_break = True
					break
			
			if _break:
				break
			
			_matches.append(root_need)
	
	return _matches

def _has_inventory_item(life, matches={}):
	return lfe.get_all_inventory_items(life, matches=[matches])

def check_all_needs(life):
	for need in life['needs']:
		need_is_met(life, need)

def need_is_met(life, need):
	_res = []
	
	for meet_callback in need['need_callback']:
		_res.extend(meet_callback(life, matches=need['need']))
	
	need['matches'] = _res
	
	if len(_res)>=need['min_matches']:
		need['num_met'] = (len(_res)-need['min_matches'])+1
		return True
	
	#logging.info('%s is not meeting a need: %s' % (' '.join(life['name']), need['need']))
	need['num_met'] = 0
	return False

def manage_hands(life):
	for item in [lfe.get_inventory_item(life, item) for item in lfe.get_held_items(life)]:
		_equip_action = {'action': 'equipitem',
				'item': item['id']}
		
		if len(lfe.find_action(life,matches=[_equip_action])):
			continue
		
		if lfe.can_wear_item(life, item):
			lfe.add_action(life,_equip_action,
				401,
				delay=lfe.get_item_access_time(life,item['id']))
			continue
		
		if not 'CANWEAR' in item['flags'] and lfe.get_all_storage(life):
			_store_action = {'action': 'storeitem',
				'item': item['id'],
				'container': lfe.get_all_storage(life)[0]['id']}
			
			if len(lfe.find_action(life,matches=[_store_action])):
				continue
			
			lfe.add_action(life,_store_action,
				401,
				delay=lfe.get_item_access_time(life,item['id']))

def manage_inventory(life):
	for item in [lfe.get_inventory_item(life, item) for item in lfe.get_all_unequipped_items(life, check_hands=False)]:
		_equip_action = {'action': 'equipitem',
				'item': item['id']}
		
		if len(lfe.find_action(life,matches=[_equip_action])):
			continue
		
		if lfe.can_wear_item(life, item):
			lfe.add_action(life,
				_equip_action,
				401,
				delay=lfe.get_item_access_time(life, item['id']))
			continue

def explore_known_chunks(life):
	#Our first order of business is to figure out exactly what we're looking for.
	#There's a big difference between exploring the map looking for a purpose and
	#exploring the map with a purpose. Both will use similar routines but I wager
	#it'll actually be a lot harder to do it without there being some kind of goal
	#to at least start us in the right direction.
	
	#This function will kick in only if the ALife is idling, so looting is handled
	#automatically.
	
	#Note: Determining whether this fuction should run at all needs to be done inside
	#the module itself.	
	_chunk_key = brain.retrieve_from_memory(life, 'explore_chunk')
	_chunk = maps.get_chunk(_chunk_key)
	
	if chunks.is_in_chunk(life, '%s,%s' % (_chunk['pos'][0], _chunk['pos'][1])):
		life['known_chunks'][_chunk_key]['last_visited'] = time.time()
		return False
	
	_pos_in_chunk = random.choice(_chunk['ground'])
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': _pos_in_chunk},200)
	return True

def _job_explore_unknown_chunks(life):
	explore_unknown_chunks(life)

def explore_unknown_chunks(life):
	if life['path']:
		return True
	
	_chunk_key = references.path_along_reference(life, 'buildings')
	
	if not _chunk_key:
		_chunk_key = references.path_along_reference(life, 'roads')
	
	if not _chunk_key:
		_best_reference = references._find_best_unknown_reference(life, 'roads')['reference']
		if not _best_reference:
			return False
		
		_chunk_key = references.find_nearest_key_in_reference(life, _best_reference, unknown=True)
	
	_walkable_area = chunks.get_walkable_areas(life, _chunk_key)
	if not _walkable_area:
		return False
	
	_closest_pos = {'pos': None, 'distance': -1}
	for pos in _walkable_area:
		_distance = numbers.distance(life['pos'], pos)
				
		if _distance <= 1:
			_closest_pos['pos'] = pos
			break
		
		if not _closest_pos['pos'] or _distance<_closest_pos['distance']:
			_closest_pos['pos'] = pos
			_closest_pos['distance'] = _distance
	
	#print _chunk_key, _closest_pos['pos']
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': _closest_pos['pos']},200)
