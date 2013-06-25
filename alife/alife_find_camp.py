from globals import *

import judgement
import camps
import stats

import logging

STATE = 'finding camp'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not 'INTELLIGENT' in life['life_flags']:
		return False
	
	if not judgement.is_safe(life):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	#if not life['camp'] and not life['known_camps'] and camps.find_best_unfounded_camp(life):
	if stats.desires_to_create_camp(life):
		if camps.find_best_unfounded_camp(life):
			return RETURN_VALUE
		else:
			print 'no unfounded camps', life['group']
	
	return False

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_best_camp = camps.find_best_unfounded_camp(life)
	print 'lets camp ;)'
	
	if not _best_camp:
		return False
	
	camps.found_camp(life, _best_camp, announce=True)
