from globals import *

import life as lfe

import references
import judgement
import movement
import camps
import maps

import logging
import random

STATE = 'camping'
INITIAL_STATES = ['idle', 'hidden']
CHECK_STATES = INITIAL_STATES[:]
CHECK_STATES.append(STATE)
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] in ['hiding', 'hidden', 'working']:
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) < ENTRY_SCORE:
		return False

	if not life['camp']:
		return False

	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_camp = life['known_camps'][life['camp']]
	if camps.is_in_camp(life, _camp):
		return False
	
	_closest_key =  references.find_nearest_key_in_reference(life, _camp['reference'])
	_chunk = maps.get_chunk(_closest_key)
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move',
		'to': random.choice(_chunk['ground'])},
		200)
