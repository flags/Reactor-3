from globals import *

import life as lfe

import action
import chunks
import goals
import maps

import random

STATE = 'working'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] in ['hiding', 'hidden', 'combat']:
		return False	
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if not lfe.execute_raw(life, 'discover', 'desires_shelter'):
		return False
	
	if not [chunk_id for chunk_id in life['known_chunks'] if chunks.get_flag(life, chunk_id, 'shelter')]:
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_shelters = [chunk_id for chunk_id in life['known_chunks'] if chunks.get_flag(life, chunk_id, 'shelter')]
	
	if _shelters:
		_shelter = chunks.get_nearest_chunk_in_list(life['pos'], _shelters)
		
		if not tuple(life['pos'][:2]) in chunks.get_flag(life, _shelter, 'shelter_cover'):
			print tuple(life['pos'][:2]),chunks.get_flag(life, _shelter, 'shelter_cover')
		
			if not lfe.path_dest(life) or (not chunks.position_is_in_chunk(lfe.path_dest(life), _shelter)):
				_cover = chunks.get_flag(life,_shelter, 'shelter_cover')
				lfe.walk_to(life, random.choice(_cover))
