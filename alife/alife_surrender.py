from globals import *

import life as lfe

import judgement
import numbers
import speech
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
	if lfe.ticker(life, 'call_for_help', 160, fire=True):
		_target = judgement.get_nearest_threat(life)
		_knows = brain.knows_alife_by_id(life, _target)
		if _target and judgement.get_nearest_trusted_target(life):
			if _knows:
				speech.announce(life, 'attacked_by_hostile', public=True, target_id=_target, last_seen_at=_knows['last_seen_at'])
			else:
				speech.announce(life, 'attacked_by_hostile', public=True, target_id=_target)
