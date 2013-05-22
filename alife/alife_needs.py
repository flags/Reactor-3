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
	
	_food = []
	_drink = []
	if brain.get_flag(life, 'hungry'):
		_food = survival.can_meet_needs(life, 'food')		
		brain.store_in_memory(life, 'possible_food', _food)
	
	if brain.get_flag(life, 'thirsty'):
		_drink = survival.can_meet_needs(life, 'drink')		
		brain.store_in_memory(life, 'possible_drink', _drink)
	
	if not _food and not _drink:
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE

	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	survival.loot(life)
	
	print 'YEAH'
