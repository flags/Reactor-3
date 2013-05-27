from globals import *

import camps

import logging

STATE = 'visiting camp'
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
	
	#Founding didn't work out...
	if life['known_camps'] and not life['camp']:
		return RETURN_VALUE
	
	return False	

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_camp = camps.get_nearest_known_camp(life)
	
	life['camp'] = _camp['id']
	#if not life['known_camps'][life['camp']]:
	#	_best_camp = camps.find_best_unfounded_camp(life)
	#	
	#	if not _best_camp:
	#		return False
	#	
	#	camps.found_camp(life, _best_camp, announce=True)
	print 'lookan'
