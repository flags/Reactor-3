from globals import *

import life as lfe

import references
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

def tick(life):
	if not 'shelter' in life['state_flags']:
		life['state_flags']['shelter'] = judgement.get_best_shelter(life)
	
	if not life['state_flags']['shelter'] in life['known_chunks']:
		judgement.judge_chunk(life, life['state_flags']['shelter'])
	
	if not chunks.get_flag(life, life['state_flags']['shelter'], 'shelter_cover'):
		return False
	
	if not list(life['pos'][:2]) in chunks.get_flag(life, life['state_flags']['shelter'], 'shelter_cover'):
		if not lfe.path_dest(life) or (not chunks.position_is_in_chunk(lfe.path_dest(life), life['state_flags']['shelter'])):
			_cover = chunks.get_flag(life, life['state_flags']['shelter'], 'shelter_cover')
			lfe.walk_to(life, random.choice(_cover))
