import life as lfe

import movement
import combat
import items
import brain
import sight

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
