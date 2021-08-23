#This is intended to be an example of how the new ALife
#system works.
from globals import *

import life as lfe

from . import judgement
from . import movement
from . import combat

import logging

STATE = 'hidden'
TIER = TIER_COMBAT-.3

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED

	if not lfe.execute_raw(life, 'state', 'hidden'):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_threat = judgement.get_nearest_threat(life)
	
	if not 'hiding' in life['state_flags']:
		movement.hide(life, _threat)
		life['state_flags']['hiding'] = True
		return True
	
	_weapon = combat.get_best_weapon(life)
	
	if _weapon:
		if not combat.weapon_equipped_and_ready(life):
			combat._equip_weapon(life, _weapon['weapon']['uid'], _weapon['feed']['uid'])
