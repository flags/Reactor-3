from globals import *

import judgement
import survival
import sight

import logging

#TODO: We need level states, so we can block
#all states from a certain level

STATE = 'looting'

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in alife_seen:
		if judgement.is_target_dangerous(life, entry['who']['life']['id']):
			_score += entry['danger']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not 'INTELLIGENT' in life['life_flags']:
		return False	
	
	#if life['state'] in INITIAL_STATES:
	if not judgement.is_safe(life):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE	
	
	if not [item['score'] for item in sight.find_visible_items(life) if item['score']]:
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	survival.loot(life)
	
