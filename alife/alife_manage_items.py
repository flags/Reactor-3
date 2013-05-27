from globals import *

import life as lfe

import judgement
import survival

import logging

STATE = 'managing'
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		if judgement.is_dangerous(life, entry['who']['life']['id']):
			_score += entry['danger']
	
	for entry in targets_not_seen:
		if judgement.is_dangerous(life, entry['who']['life']['id']):
			_score += entry['danger']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] in ['looting']:
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen)<0:
		return False
	
	#if not lfe.get_all_unequipped_items(life):
	#	return False
	if lfe.get_open_hands(life):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	#survival.manage_inventory(life)
	survival.manage_hands(life)
