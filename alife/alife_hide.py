#This is intended to be an example of how the new ALife
#system works.
from globals import *

import judgement
import movement

import logging

STATE = 'hiding'
INITIAL_STATES = ['idle', 'hidden']
CHECK_STATES = INITIAL_STATES[:]
CHECK_STATES.append(STATE)

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		if judgement.is_target_dangerous(life, entry['who']['life']['id']):
			_score += entry['danger']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if judgement.is_safe(life):
		return False
	
	if not judgement.get_visible_threats(life):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_threat = judgement.get_nearest_threat(life)
	movement.escape(life, LIFE[_threat], source_map)
