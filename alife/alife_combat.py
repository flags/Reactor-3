from globals import *

import graphics as gfx
import life as lfe

import judgement
import numbers
import combat
import speech
import sight
import camps
import brain
import stats
import logic
import jobs

import logging

STATE = 'combat'
TIER = TIER_COMBAT-.4

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	_mode = None
	if lfe.execute_raw(life, 'state', 'combat'):
		_mode = 'combat'
	
	if not _mode and lfe.execute_raw(life, 'state', 'hunt'):
		_mode = 'hunt'
	
	if not _mode:
		return False
	
	if not lfe.execute_raw(life, 'combat', 'ranged') and not lfe.execute_raw(life, 'combat', 'melee'):
		return False
	
	if not life['state'] == STATE:
		life['state_flags'] = {}
		stats.battle_cry(life)
		
		if gfx.position_is_in_frame(life['pos']) and SETTINGS['controlling']:
			_can_see = sight.can_see_position(life, LIFE[SETTINGS['controlling']]['pos'])
			
			if _can_see:
				_knows = brain.knows_alife_by_id(life, SETTINGS['controlling'])
				
				if _knows and judgement.can_trust(life, SETTINGS['controlling']):
					if lfe.ticker(life, 'enter_combat_message', 3, fire=True):
						logic.show_event('%s readies up.' % ' '.join(life['name']), life=life)
		
		RETURN_VALUE = STATE_CHANGE
	
	brain.flag(life, 'combat_mode', value=_mode)
	
	return RETURN_VALUE

def ranged_attack(life):
	_all_targets = judgement.get_threats(life, ignore_escaped=1)
	
	combat.ranged_combat(life, _all_targets)

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_all_targets = judgement.get_threats(life, ignore_escaped=1)
	
	if lfe.execute_raw(life, 'combat', 'ranged_ready', break_on_true=True, break_on_false=False):
		combat.ranged_combat(life, _all_targets)

	if lfe.execute_raw(life, 'combat', 'melee_ready', break_on_true=True, break_on_false=False):
		combat.melee_combat(life, _all_targets)