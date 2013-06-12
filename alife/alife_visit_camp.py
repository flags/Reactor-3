from globals import *

import judgement
import camps

import logging

STATE = 'visiting camp'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED

	if not 'INTELLIGENT' in life['life_flags']:
		return False	
	
	if not judgement.is_safe(life):
		return False	
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
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
