#This is intended to be an example of how the new ALife
#system works.
from globals import *

import movement

import logging

STATE = 'hiding'
INITIAL_STATES = ['idle','hidden']
CHECK_STATES = INITIAL_STATES[:]
CHECK_STATES.append(STATE)
EXIT_SCORE = -75
ENTRY_SCORE = -100

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in alife_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] in INITIAL_STATES:
		if not calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) <= ENTRY_SCORE:
			return False
		
		RETURN_VALUE = STATE_CHANGE
	elif not life['state'] in CHECK_STATES:
		return False		
	
	if not len(targets_seen):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	movement.escape(life, targets_seen[0]['who'], source_map)
