#This is intended to be an example of how the new ALife
#system works.
from globals import *

import survival
import sight

import logging

#TODO: We need level states, so we can block
#all states from a certain level

STATE = 'exploring'
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in alife_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
		
	if life['state'] == 'looting':
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if len(targets_seen):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	survival.loot(life)
	
