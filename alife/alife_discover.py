from globals import *

import life as lfe

import judgement
import survival
import chunks
import sight

import logging

STATE = 'discovering'

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
	
	if life['state'] in ['exploring', 'looting', 'managing', 'finding camp', 'camping', 'working', 'visiting camp', 'needs', 'hiding']:
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
		return False
	
	#if chunks.find_best_known_chunk(life):
	#	return False
	
	#if not chunks.find_best_unknown_chunk(life, chunks.find_surrounding_unknown_chunks(life)):
	#	return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	survival.explore_unknown_chunks(life)
	
