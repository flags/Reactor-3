from globals import *

import life as lfe

import judgement
import movement
import survival
import brain

STATE = 'needs'

TIER = TIER_SURVIVAL

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED

	if not judgement.is_safe(life):
		return False

	_needs_to_meet = []
	for need in life['needs']:
		if not survival.is_need_active(life, need):
			continue
		
		if not survival.can_meet_need(life, need):
			lfe.create_question(life,
				'wants item',
				{'item': need['need']},
				lfe.get_all_inventory_items,
				need['need'])
			continue
		
		_needs_to_meet.append(need)

	if not _needs_to_meet:
		return False
	
	brain.store_in_memory(life, 'needs_to_meet', _needs_to_meet)

	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE

	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if lfe.is_consuming(life):
		return True

	_needs_to_meet = brain.retrieve_from_memory(life, 'needs_to_meet')
	
	for need in _needs_to_meet:
		if survival.need_is_met(life, need):
			need['satisfy_callback'](life, need['matches'][0]['id'])
			return True
		
		if need['can_meet_with']:
			movement.collect_nearby_wanted_items(life, visible=False, matches=need['can_meet_with'][0]['item'])
			return True