#This is intended to be an example of how the new ALife
#system works.
from globals import *

import movement
import combat

import logging

STATE = 'hidden'
INITIAL_STATE = 'hiding'
EXIT_SCORE = -75
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in alife_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] == INITIAL_STATE:
		if not calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) <= ENTRY_SCORE:
			return False
		
		RETURN_VALUE = STATE_CHANGE
	elif not life['state'] in [INITIAL_STATE, STATE]:
		return False		
	
	if len(targets_seen):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	if combat.has_weapon(life):
		if not combat._weapon_equipped_and_ready(life):
				if not 'equipping' in life:
					if combat._equip_weapon(life):
						life['equipping'] = True
