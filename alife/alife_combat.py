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

def setup(life):
	brain.store_in_memory(life, 'targets', judgement.get_targets(life))	

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	_all_targets = []
	_combat_targets = judgement.get_targets(life)
	
	if not _combat_targets:
		return False
	
	if not brain.retrieve_from_memory(life, 'combat_targets'):
		return False
	
	if not lfe.execute_raw(life, 'combat', 'ranged') and not lfe.execute_raw(life, 'combat', 'melee'):
		return False
	
	if not life['state'] == STATE:
		stats.battle_cry(life)
		
		if gfx.position_is_in_frame(life['pos']):
			_can_see = sight.can_see_position(LIFE[SETTINGS['controlling']], life['pos'])
			
			if _can_see:
				_knows = brain.knows_alife_by_id(LIFE[SETTINGS['controlling']], life['id'])
				
				if _knows and judgement.can_trust(LIFE[SETTINGS['controlling']], life['id']):
					if lfe.ticker(life, 'enter_combat_message', 3, fire=True):
						logic.show_event('%s readies up.' % ' '.join(life['name']), life=life)
				
				#gfx.highlight_tiles(_can_see)
		
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_VALUE

#TODO: Use judgement.get_nearest_threat()
def get_closest_target(life, targets):
	_closest = {'dist': -1, 'life': None}
	
	for target in targets:
		_know = brain.knows_alife_by_id(life, target)
		_dist = numbers.distance(life['pos'], _know['last_seen_at'])
		
		if _dist<_closest['dist'] or not _closest['life']:
			_closest['life'] = target
			_closest['dist'] = _dist
	
	return _closest['life']

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_all_targets = brain.retrieve_from_memory(life, 'combat_targets')
	
	if lfe.execute_raw(life, 'combat', 'ranged_ready', break_on_true=True, break_on_false=False):
		#_closest_target = get_closest_target(life, _all_targets)
		combat.ranged_combat(life, _all_targets)

	if lfe.execute_raw(life, 'combat', 'melee_ready', break_on_true=True, break_on_false=False):
		_closest_target = get_closest_target(life, _all_targets)
		combat.melee_combat(life, _all_targets)