from globals import *

import life as lfe

import references
import judgement
import chunks
import groups
import brain
import camps
import stats
import maps

import logging
import random

STATE = 'finding camp'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not judgement.is_safe(life):
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if stats.desires_to_create_camp(life):
		_unfounded_camp = camps.find_best_unfounded_camp(life, ignore_fully_explored=True)
		
		if _unfounded_camp['score'] >= stats.get_minimum_camp_score(life):
			brain.store_in_memory(life, 'explore_camp', None)
			return RETURN_VALUE
		elif _unfounded_camp['camp']:
			brain.store_in_memory(life, 'explore_camp', _unfounded_camp['camp'])
			print 'only interested in camp (exploring)'
			return RETURN_VALUE

	return False

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_to_explore = brain.retrieve_from_memory(life, 'explore_camp')
	if _to_explore:
		logging.warning('%s is looking for a camp (possible crash incoming)' % ' '.join(life['name']))
		_closest_key =  references.find_nearest_key_in_reference(life, _to_explore, unknown=True)
		_chunk = maps.get_chunk(_closest_key)
		_dest = lfe.path_dest(life)
		
		if not _dest or not chunks.position_is_in_chunk(_dest, _closest_key):
			_pos = random.choice(_chunk['ground'])
			print _pos
			lfe.clear_actions(life)
			lfe.add_action(life,{'action': 'move',
				'to': _pos}, 200)
		return True
	
	_best_camp = camps.find_best_unfounded_camp(life)['camp']
	
	if not _best_camp:
		return False
	
	camps.found_camp(life, _best_camp, announce=False)
	if life['group'] and groups.is_leader(life['group'], life['id']):
		groups.set_camp(life['group'], camps.get_camp_via_reference(_best_camp))
