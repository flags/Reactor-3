from globals import *

import life as lfe

import judgement
import numbers
import brain
import stats

import logging

STATE = 'surrender'
TIER = TIER_SUBMIT

STATE_ICONS[STATE] = chr(25)

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not lfe.execute_raw(life, 'state', 'surrender'):
		return False

	if not life['state'] == STATE:
		lfe.stop(life)
		lfe.say(life, '@n gives up.', action=True)
		
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	#_all_targets = judgement.get_combat_targets(life)
	
	pass
	
	#if lfe.execute_raw(life, 'combat', 'ranged_ready', break_on_true=True, break_on_false=False):
	#	_closest_target = get_closest_target(life, _all_targets)
	#	combat.ranged_combat(life, _closest_target)

	#if lfe.execute_raw(life, 'combat', 'melee_ready', break_on_true=True, break_on_false=False):
	#	_closest_target = get_closest_target(life, _all_targets)
	#	combat.melee_combat(life, _closest_target)