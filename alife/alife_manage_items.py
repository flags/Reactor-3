from globals import *

import life as lfe

import judgement
import survival

import logging

STATE = 'managing'
TIER = TIER_SURVIVAL-.3

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not lfe.execute_raw(life, 'state', 'managing'):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	#if lfe.get_open_hands(life):
	#	return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	survival.manage_inventory(life)
	#survival.manage_hands(life)
