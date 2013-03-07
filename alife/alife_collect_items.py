from globals import *

import survival
import sight

import logging

#TODO: We need level states, so we can block
#all states from a certain level

STATE = 'looting'
INITIAL_STATES = ['idle', 'talking']
CHECK_STATES = INITIAL_STATES[:]
CHECK_STATES.append(STATE)
EXIT_SCORE = -75
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in alife_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] in INITIAL_STATES:
		if not calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) >= ENTRY_SCORE:
			return False
		
		RETURN_VALUE = STATE_CHANGE
	elif not life['state'] in CHECK_STATES:
		return False		
	
	if len(targets_seen):
		return False
	
	_score = 0
	#print sight.find_visible_items(life)
	#if not sight.find_visible_items(life):
	#	return False
	if not [item['score'] for item in sight.find_visible_items(life) if item['score']]:
		return False
	
	#if not _score:
	#	print 'nothing!!!!'
	#	return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	survival.loot(life)
	
