from globals import *
import life as lfe

import references
import judgement
import movement
import rawparse
import weapons
import action
import chunks
import speech
import combat
import brain
import items
import sight
import stats
import maps

import logging
import numbers
import random
import time

def _get_need_amount(life, need):
	if need['amount_callback']:
		return need['amount_callback'](life, need)
	
	if need['amount']:
		return need['amount']

def add_needed_item(life, matching, amount=1, amount_callback=None, pass_if=[], satisfy_if=None, satisfy_callback=None):
	life['needs'][str(life['need_id'])] = {'type': 'item',
	                      'match': matching,
	                      'meet_with': [],
	                      'could_meet_with': [],
	                      'amount': amount,
	                      'amount_callback': amount_callback,
	                      'pass_if': pass_if,
	                      'satisfy_if': satisfy_if,
	                      'satisfy_callback': satisfy_callback}
	
	logging.debug('Added item need: %s' % matching)
	
	life['need_id'] += 1
	return str(life['need_id']-1)

def delete_needed_item(life, need_id):
	del life['needs'][need_id]
	
	logging.debug('Remove item need: %s' % need_id)

def remove_item_from_needs(life, item_uid):
	for need in life['needs'].values():
		if item_uid in need['meet_with']:
			need['meet_with'].remove(item_uid)
		
		if item_uid in need['could_meet_with']:
			need['could_meet_with'].remove(item_uid)

#@profile
def process(life):
	for need in life['needs'].values():
		if need['type'] == 'item':
			_has_items = []
			_potential_items = []
			
			for item in brain.get_matching_remembered_items(life, need['match'], no_owner=True):
				if brain.get_item_flag(life, ITEMS[item], 'ignore'):
					continue
				
				_potential_items.append(item)
				
			for item in lfe.get_all_inventory_items(life, matches=[need['match']]):
				_has_items.append(item['uid'])
			
			if len(_has_items) >= _get_need_amount(life, need):
				need['meet_with'] = _has_items
			elif _potential_items:
				need['could_meet_with'] = _potential_items
			else:
				need['meet_with'] = []
				need['could_meet_with'] = []

def is_need_met(life, need):
	if need['meet_with']:
		return True
	
	return False

def needs_to_satisfy(life, need):
	for requirement in need['pass_if']:
		if action.execute_small_script(life, requirement):
			return False
	
	return action.execute_small_script(life, need['satisfy_if'])

def can_satisfy(life, need):
	if not is_need_met(life, need):
		return False
	
	return True

def can_potentially_satisfy(life, need):
	return need['could_meet_with']

def satisfy(life, need):
	if action.execute_small_script(life, need['satisfy_if']):
		if need['type'] == 'item':
			_callback = action.execute_small_script(life, need['satisfy_callback'])
			_callback(life, need['meet_with'][0])
			return True
	
	return False

#TODO: Remove reference from dialog and delete
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

def has_unmet_needs(life):
	if len(brain.retrieve_from_memory(life, 'needs_unmet'))>0:
		return True
	
	return False

def has_needs_to_meet(life):
	_needs = brain.retrieve_from_memory(life, 'needs_to_meet')
	
	if not _needs:
		return False
	
	if len(_needs)>0:
		return True
	
	return False

def has_needs_to_satisfy(life):
	_needs = brain.retrieve_from_memory(life, 'needs_to_satisfy')
	
	if _needs:
		return True
	
	return False

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
		need['num_above_needed'] = (len(_res)-need['min_matches'])+1
		return True
	
	#logging.info('%s is not meeting a need: %s' % (' '.join(life['name']), need['need']))
	need['num_above_needed'] = 0
	return False

def generate_needs(life):
	if not lfe.ticker(life, 'generate_needs', 90, fire=True):
		return False
	
	if stats.desires_weapon(life):
		brain.flag(life, 'no_weapon')
	else:
		brain.unflag(life, 'no_weapon')
	
	if combat.get_weapons(life):
		for weapon in combat.get_weapons(life):
			_weapon_uid = weapon['uid']
			
			#for _flag in ['ammo', 'feed']:
			if len(combat.get_all_ammo_for_weapon(life, _weapon_uid))>=5:
				_flag_name = '%s_needs_ammo' % _weapon_uid
				
				_need = brain.get_flag(life, _flag_name)
				
				if _need:
					delete_needed_item(life, _need)
					brain.unflag(life, _flag_name)
			
			if combat.get_feeds_for_weapon(life, _weapon_uid):
				_flag_name = '%s_needs_feed' % _weapon_uid
				
				_need = brain.get_flag(life, _flag_name)
				
				if _need:
					delete_needed_item(life, _need)
					brain.unflag(life, _flag_name)
		
		if not combat.has_potentially_usable_weapon(life) and not combat.has_ready_weapon(life):
			#_weapon_with_feed = None
			#for weapon in combat.get_weapons(life):
			#	if weapons.get_feed(weapon):
			#		_weapon_with_feed = weapon['uid']
			#		break
			
			#if _weapon_with_feed:
			#	_weapon_uid = weapon['uid']
			#	_flag_name = '%s_needs_ammo' % _weapon_uid
			#	_n = add_needed_item(life,
			#	                     {'type': 'bullet', 'owner': None, 'ammotype': weapon['ammotype']},
			#	                     satisfy_if=action.make_small_script(function='get_flag',
			#	                                                         args={'flag': _flag_name}),
			#	                     satisfy_callback=action.make_small_script(return_function='pick_up_and_hold_item'))
			#	
			#	brain.flag(life, _flag_name, value=_n)
			
			for weapon in combat.get_weapons(life):
				_weapon_uid = weapon['uid']
				_flag_name = '%s_needs_feed' % _weapon_uid
				if combat.have_feed_and_ammo_for_weapon(life, _weapon_uid):
					continue
				
				#print 'feeds?', combat.get_feeds_for_weapon(life, _weapon_uid), [ITEMS[i]['name'] for i in lfe.get_held_items(life)]
				
				if not combat.get_feeds_for_weapon(life, _weapon_uid) and not brain.get_flag(life, _flag_name):
					_n = add_needed_item(life,
				                         {'type': weapon['feed'], 'owner': None, 'ammotype': weapon['ammotype']},
				                         satisfy_if=action.make_small_script(function='get_flag',
				                                                             args={'flag': _flag_name}),
				                         satisfy_callback=action.make_small_script(return_function='pick_up_and_hold_item'))

					brain.flag(life, _flag_name, value=_n)
			
				_flag_name = '%s_needs_ammo' % _weapon_uid
				
				if len(combat.get_all_ammo_for_weapon(life, _weapon_uid))<5 and not brain.get_flag(life, _flag_name):
					_n = add_needed_item(life,
						                 {'type': 'bullet', 'owner': None, 'ammotype': weapon['ammotype']},
						                 satisfy_if=action.make_small_script(function='get_flag',
						                                                     args={'flag': _flag_name}),
						                 satisfy_callback=action.make_small_script(return_function='pick_up_and_hold_item'))
					
					brain.flag(life, _flag_name, value=_n)

def manage_hands(life):
	for item in [lfe.get_inventory_item(life, item) for item in lfe.get_held_items(life)]:
		judgement.judge_item(life, item['uid'])
		_known_item = brain.get_remembered_item(life, item['uid'])
		
		if _known_item['score']:#judgement.get_score_of_highest_scoring_item(life):
			continue
		
		_equip_action = {'action': 'equipitem',
				'item': item['uid']}
		
		if len(lfe.find_action(life, matches=[_equip_action])):
			return True
		
		if lfe.can_wear_item(life, item['uid']):
			lfe.add_action(life, _equip_action,
				401,
				delay=lfe.get_item_access_time(life, item['uid']))
			return True
		
		_storage = lfe.can_put_item_in_storage(life, item['uid'])
		if not 'CAN_WEAR' in item['flags'] and _storage:
			_store_action = {'action': 'storeitem',
				'item': item['uid'],
				'container': _storage}
			
			if len(lfe.find_action(life, matches=[_store_action])):
				continue
			
			lfe.add_action(life,_store_action,
				401,
				delay=lfe.get_item_access_time(life, item['uid']))
			return True
	
	return False

def manage_inventory(life):
	if manage_hands(life):
		return False
	
	for weapon_uid in combat.get_equipped_weapons(life):
		if not combat.weapon_is_working(life, weapon_uid):
			if combat.weapon_is_in_preferred_working_condition(life, weapon_uid):
				combat.reload_weapon(life, weapon_uid)
				return True
	
	_item_to_wear = {'score': 0, 'item_uid': None}
	_item_to_equip = {'score': 0, 'item_uid': None}
		
	for item in [lfe.get_inventory_item(life, item) for item in lfe.get_all_unequipped_items(life)]:
		judgement.judge_item(life, item['uid'])
		_known_item = brain.get_remembered_item(life, item['uid'])
		
		if _known_item['score']:
			if lfe.can_wear_item(life, item['uid']):
				if _known_item['score'] > _item_to_wear['score']:
					_item_to_wear['score'] = _known_item['score']
					_item_to_wear['item_uid'] = item['uid']
			else:
				if rawparse.raw_has_section(life, 'items') and rawparse.raw_section_has_identifier(life, 'items', item['type']):
					_action = lfe.execute_raw(life, 'items', item['type'])
					
					if _action == 'equip':
						if _known_item['score'] > _item_to_equip['score']:
							_item_to_equip['score'] = _known_item['score']
							_item_to_equip['item_uid'] = item['uid']
	
	_item = None
	if _item_to_wear['score'] > _item_to_equip['score']:
		_item = _item_to_wear['item_uid']
	elif _item_to_equip['item_uid']:
		_item = _item_to_equip['item_uid']
	
	if _item:
		_equip_action = {'action': 'equipitem', 'item': _item}
		
		if len(lfe.find_action(life, matches=[_equip_action])):
			return False
		
		lfe.add_action(life,
			_equip_action,
			401,
			delay=lfe.get_item_access_time(life, _item))
		
		return True
	
	return False

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
	
	if life['path'] and chunks.position_is_in_chunk(lfe.path_dest(life), _chunk_key):
		return True
	
	if chunks.is_in_chunk(life, '%s,%s' % (_chunk['pos'][0], _chunk['pos'][1])):
		life['known_chunks'][_chunk_key]['last_visited'] = WORLD_INFO['ticks']
		return False
	
	if not _chunk['ground']:
		return False
	
	_pos_in_chunk = random.choice(_chunk['ground'])
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': _pos_in_chunk},200)
	return True

def explore_unknown_chunks(life):
	if life['path']:
		return True
	
	_chunk_key = references.path_along_reference(life, 'roads')
	
	if not _chunk_key:
		_best_reference = WORLD_INFO['reference_map']['roads'][0]
		
		if not _best_reference:
			return False
		
		_chunk_key = references.find_nearest_key_in_reference(life, _best_reference, unknown=True, threshold=15)
	
	if not _chunk_key:
		return False
	
	_walkable_area = chunks.get_walkable_areas(_chunk_key)
	if not _walkable_area:
		print 'no walkable area'
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
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': _closest_pos['pos']},200)
	
	return True
