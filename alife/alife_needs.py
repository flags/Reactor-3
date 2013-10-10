from globals import *

import life as lfe

import judgement
import movement
import survival
import brain

STATE = 'needs'

TIER = TIER_SURVIVAL

def setup(life):
	_needs_to_meet = []
	_needs_to_satisfy = []
	
	for need in life['needs'].values():
		if not survival.needs_to_satisfy(life, need):
			continue
		
		if survival.can_satisfy(life, need):
			_needs_to_satisfy.append(need)
		
		if not survival.can_satisfy(life, need) and not survival.can_potentially_satisfy(life, need):
			continue
		
		_needs_to_meet.append(need)

	brain.store_in_memory(life, 'needs_to_meet', _needs_to_meet)
	brain.store_in_memory(life, 'needs_to_satisfy', _needs_to_satisfy)

	if not _needs_to_meet and not _needs_to_satisfy:
		return False

def get_tier(life):
	if lfe.execute_raw(life, 'state', 'needs'):
		return TIER_SURVIVAL-.2
	
	return TIER

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED

	if not judgement.is_safe(life):
		return False

	if not brain.retrieve_from_memory(life, 'needs_to_meet') and not brain.retrieve_from_memory(life, 'needs_to_satisfy'):
		return False

	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE

	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if life['actions']:
		return True

	_needs_to_meet = brain.retrieve_from_memory(life, 'needs_to_meet')
	
	for need in _needs_to_meet:
		movement.collect_nearby_wanted_items(life, matches=need['match'], only_visible=False)
		break
	
	_needs_to_satisfy = brain.retrieve_from_memory(life, 'needs_to_satisfy')
	
	for need in _needs_to_satisfy:
		print 'need to be'
		print survival.satisfy(life, need)
