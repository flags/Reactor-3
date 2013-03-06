from globals import *

import life as lfe

import survival
import chunks
import sight

import logging

STATE = 'exploring'
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		_score += entry['score']
	
	for entry in targets_not_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] == 'looting':
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen)<0:
		return False
	
	if not chunks.find_best_chunk(life):
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	survival.explore_known_chunks(life)
	
