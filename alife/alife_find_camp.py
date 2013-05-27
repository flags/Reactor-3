from globals import *

import judgement
import camps

import logging

STATE = 'finding camp'
INITIAL_STATES = ['idle', 'hidden']
CHECK_STATES = INITIAL_STATES[:]
CHECK_STATES.append(STATE)
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		_score += entry['danger']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) < ENTRY_SCORE:
		return False
	
	if not life['camp'] and not life['known_camps'] and camps.find_best_unfounded_camp(life):
		return RETURN_VALUE
	#if not life['known_camps'] and camps.find_best_unfounded_camp(life):
	#	return RETURN_VALUE
	
	return False	

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_best_camp = camps.find_best_unfounded_camp(life)
	
	if not _best_camp:
		return False
	
	camps.found_camp(life, _best_camp, announce=True)
