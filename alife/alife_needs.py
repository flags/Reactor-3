from globals import *

import life as lfe

import survival
import brain

STATE = 'needs'
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) < ENTRY_SCORE:
		return False
	
	_has_food = lfe.get_all_inventory_items(life, matches=[{'type': 'food'}])
	_has_drink = lfe.get_all_inventory_items(life, matches=[{'type': 'drink'}])
	brain.store_in_memory(life, 'has_food', _has_food)
	brain.store_in_memory(life, 'has_drink', _has_drink)
	
	_food = []
	_drink = []
	if brain.get_flag(life, 'hungry'):
		_food = survival.can_meet_needs(life, 'food')
		brain.store_in_memory(life, 'possible_food', _food)
	
	if brain.get_flag(life, 'thirsty'):
		_drink = survival.can_meet_needs(life, 'drink')
		brain.store_in_memory(life, 'possible_drink', _drink)
	
	if not _food and not _drink and not _has_food and not _has_drink:
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE

	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if lfe.is_consuming(life):
		return True
	
	if brain.get_flag(life, 'hungry'):
		_food = brain.retrieve_from_memory(life, 'has_food')
		
		if _food:
			lfe.consume(life, _food[0]['id'])
			return True
		else:
			lfe.create_question(life,
				'wants item',
				{'item': {'type': 'food'}},
				lfe.get_all_inventory_items,
				{'type': 'food'})
		
	if brain.get_flag(life, 'thirsty'):
		_drinks = brain.retrieve_from_memory(life, 'has_drink')
		
		if _drinks:
			lfe.consume(life, _drinks[0]['id'])
			return True
		else:
			lfe.create_question(life,
				'wants item',
				{'item': {'type': 'drink'}},
				lfe.get_all_inventory_items,
				{'type': 'drink'})
	
	survival.manage_needs(life)