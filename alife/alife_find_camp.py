from globals import *

import judgement
import brain
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
	
	if stats.desires_to_create_camp(life):
		_unfounded_camp = camps.find_best_unfounded_camp(life)
		
		if _unfounded_camp['score'] >= stats.get_minimum_camp_score(life):
			print 'YO!!!! LETS CAMP, DUDE!'
			return RETURN_VALUE
		else:
			brain.store_in_memory(life, 'explore_camp', _unfounded_camp['camp'])
			print 'only interested'
		
		#else:
		#	print 'no unfounded camps', life['group']
	
	return False

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_best_camp = camps.find_best_unfounded_camp(life)['camp']
	print 'lets camp ;)'
	
	if not _best_camp:
		return False
	
	camps.found_camp(life, _best_camp, announce=True)
