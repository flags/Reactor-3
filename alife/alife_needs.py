from globals import *

import life as lfe

import judgement
import survival
import brain

STATE = 'needs'

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0

	for entry in targets_seen:
		if judgement.is_target_dangerous(life, entry['who']['life']['id']):
			_score += entry['danger']

	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED

	if not judgement.is_safe(life):
		return False

	_needs_to_meet = []
	for need in life['needs']:
		if not survival.is_need_active(life, need):
			print life['name'], 'Need not active:', need['need']
			continue
			
		if survival.need_is_met(life, need):
			continue
		
		if not survival.can_meet_need(life, need):
			print life['name'],'Need not being met:', need['need']
			continue
		
		_needs_to_meet.append(need)
	
	#_has_food = []
	#_has_drink = []
	#_possible_food = []
	#_possible_drink = []
	#if brain.get_flag(life, 'hungry'):
		#_possible_food = survival.can_meet_needs(life, 'food')
		#_has_food = lfe.get_all_inventory_items(life, matches=[{'type': 'food'}])
		#brain.store_in_memory(life, 'possible_food', _possible_food)
		#brain.store_in_memory(life, 'has_food', _has_food)
	#else:
		#brain.store_in_memory(life, 'possible_food', [])
		#brain.store_in_memory(life, 'has_food', [])

	#if brain.get_flag(life, 'thirsty'):
		#_possible_drink = survival.can_meet_needs(life, 'drink')
		#_has_drink = lfe.get_all_inventory_items(life, matches=[{'type': 'drink'}])
		#brain.store_in_memory(life, 'possible_drink', _possible_drink)
		#brain.store_in_memory(life, 'has_drink', _has_drink)
	#else:
		#brain.store_in_memory(life, 'possible_drink', [])
		#brain.store_in_memory(life, 'has_drink', [])

	if not _needs_to_meet:
		return False
	
	brain.store_in_memory(life, 'needs_to_meet', _needs_to_meet)

	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE

	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if lfe.is_consuming(life):
		return True

	_needs_to_meet = brain.retrieve_from_memory(life, 'needs_to_meet')
	
	for need in _needs_to_meet:
		print len(need['matches']),len(need['can_meet_with'])

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

	if brain.retrieve_from_memory(life, 'possible_food') or brain.retrieve_from_memory(life, 'possible_drink'):
		print 'Manage...',life['name']
		survival.manage_needs(life)