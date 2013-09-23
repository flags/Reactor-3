from globals import *

import life as lfe

import judgement
import chunks
import goals
import maps

import random

STATE = 'shelter'
TIER = TIER_SURVIVAL-.1

def get_tier(life):
	if not lfe.execute_raw(life, 'discover', 'desires_shelter') and lfe.execute_raw(life, 'state', 'shelter'):
		return TIER_IDLE-.1
	
	return TIER

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if not lfe.execute_raw(life, 'discover', 'desires_shelter') and not lfe.execute_raw(life, 'state', 'shelter'):
		return False
	
	if not [chunk_id for chunk_id in life['known_chunks'] if chunks.get_flag(life, chunk_id, 'shelter')]:
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if not 'shelter' in life['state_flags']:
		life['state_flags']['shelter'] = judgement.get_best_shelter(life)
	
	if not chunks.get_flag(life, life['state_flags']['shelter'], 'shelter_cover'):
		return False
	
	if not list(life['pos'][:2]) in chunks.get_flag(life, life['state_flags']['shelter'], 'shelter_cover'):
		if not lfe.path_dest(life) or (not chunks.position_is_in_chunk(lfe.path_dest(life), life['state_flags']['shelter'])):
			_cover = chunks.get_flag(life, life['state_flags']['shelter'], 'shelter_cover')
			lfe.walk_to(life, random.choice(_cover))
