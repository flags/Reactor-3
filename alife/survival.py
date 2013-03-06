import life as lfe

import movement
import combat
import items
import brain
import sight
import maps
import time

def loot(life):
	#What do we need to do?
	#	- Get items?
	#	- Find shelter?
	
	manage_inventory(life)
	
	if combat.has_weapon(life):
		brain.unflag(life, 'no_weapon')
	else:
		brain.flag(life, 'no_weapon')
	
	if lfe.get_all_inventory_items(life, matches=[{'type': 'backpack'}]):
		brain.unflag(life, 'no_backpack')
	else:
		brain.flag(life, 'no_backpack')
	
	if brain.get_flag(life, 'no_weapon'):
		_nearby_weapons = sight.find_known_items(life, matches=[{'type': 'gun'}])
		
		if _nearby_weapons:
			movement.collect_nearby_wanted_items(life, matches=[{'type': 'gun'}])
	
	if not brain.get_flag(life, 'no_weapon'):
		_ammo_matches = []
		_feed_matches = []
		for weapon in combat.has_weapon(life):
			_ammo_matches.append({'type': 'bullet','ammotype': weapon['ammotype']})
			_feed_matches.append({'type': weapon['feed'],'ammotype': weapon['ammotype']})
		
		if sight.find_known_items(life, matches=_ammo_matches):
			movement.collect_nearby_wanted_items(life, matches=_ammo_matches)
		elif sight.find_known_items(life, matches=_feed_matches):
			movement.collect_nearby_wanted_items(life, matches=_feed_matches)
	
	if brain.get_flag(life, 'no_backpack'):
		_nearby_backpacks = sight.find_known_items(life, matches=[{'type': 'backpack'}])
		
		if _nearby_backpacks:
			movement.collect_nearby_wanted_items(life, matches=[{'type': 'backpack'}])

def manage_inventory(life):
	_empty_hand = lfe.get_open_hands(life)
	
	if not _empty_hand:
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

def explore(life):
	#Our first order of business is to figure out exactly what we're looking for.
	#There's a big difference between exploring the map looking for a purpose and
	#exploring the map with a purpose. Both will use similar routines but I wager
	#it'll actually be a lot harder to do it without there being some kind of goal
	#to at least start us in the right direction.
	
	#This function will kick in only if the ALife is idling, so looting is handled
	#automatically.
	
	#Note: Determining whether this fuction should run at all needs to be done inside
	#the module itself.
	_interesting_chunks = {}
	
	for chunk_key in life['judged_chunks']:
		_chunk = life['judged_chunks'][chunk_key]
		
		if _chunk['last_visited'] == 0 or time.time()-_chunk['last_visited']>=900:
			_interesting_chunks[chunk_key] = life['judged_chunks'][chunk_key]
	
	_chunk_key = _interesting_chunks.keys()[0]
	_chunk = maps.get_chunk(_chunk_key)
	
	print life['pos'],_chunk['pos']
	
	if lfe.is_in_chunk(life, '%s,%s' % (_chunk['pos'][0], _chunk['pos'][1])):
		life['judged_chunks'][_chunk_key]['last_visited'] = time.time()
	
	_pos_in_chunk = maps.get_open_position_in_chunk(life['map'], _interesting_chunks.keys()[0])
	
	lfe.add_action(life,{'action': 'move','to': _pos_in_chunk},200)
