from globals import *

import life as lfe

import judgement
import movement
import groups
import speech
import action
import events
import brain
import stats
import jobs

TIER = TIER_PASSIVE

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	return RETURN_SKIP

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if not life['group']:
		if not stats.desires_to_create_group(life):
			return False
		
		groups.create_group(life)
		return False
	
	if not groups.is_leader_of_any_group(life):
		return False
	
	_group = groups.get_group(life, life['group'])
	
	#if groups.needs_resources(life['group']):
	#
	
	groups.find_and_announce_shelter(life, life['group'])
	
	#if groups.get_shelter(life, life['group']):
	groups.manage_resources(life, life['group'])