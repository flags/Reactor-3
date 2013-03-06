from globals import *

import life as lfe

import combat

import weapons
import logging
import numbers
import time

def judge_item(life, item):
	_score = 0
	
	_has_weapon = combat.is_weapon_equipped(life)
	
	if not _has_weapon and item['type'] == 'gun':
		_score += 30
	elif _has_weapon and item['type'] == _has_weapon['feed'] and item['ammotype'] == _has_weapon['ammotype']:
		_score += 20
	else:
		_score += 10
	
	return _score

def judge_self(life):
	_confidence = 0
	_limb_confidence = 0
	
	for limb in [life['body'][limb] for limb in life['body']]:
		#TODO: Mark as target?
		if not limb['bleeding']:
			_limb_confidence += 1
		
		if not limb['bruised']:
			_limb_confidence += 2
		
		if not limb['broken']:
			_limb_confidence += 3
	
	#TODO: There's a chance to fake confidence here
	#If we're holding a gun, that's all the other ALifes see
	#and they judge based on that (unless they've heard you run
	#out of ammo.)
	#For now we'll consider ammo just because we can...
	_self_armed = lfe.get_held_items(life,matches=[{'type': 'gun'}])
	
	if _self_armed:
		_weapon = lfe.get_inventory_item(life,_self_armed[0])
		_feed = weapons.get_feed(_weapon)
		
		if _feed and _feed['rounds']:
			_confidence += 30
		else:
			_confidence -= 30
	
	return _confidence+_limb_confidence

def judge(life, target):
	_like = 0
	_dislike = 0
	
	if target['life']['asleep']:
		return 0
	
	print target['consider']
	
	if 'surrender' in target['consider']:
		return 0
	
	if 'greeted' in target['consider']:
		_like += 1
	
	if 'insulted' in target['consider']:
		_dislike += 1
	
	return _like-_dislike

def judge_chunk(life, chunk_key):
	chunk = CHUNK_MAP[chunk_key]
	
	if chunk['type'] == 'grass':
		return False
	
	if not chunk_key in life['judged_chunks']:
		life['judged_chunks'][chunk_key] = {'last_visited': 0}
	
	_score = numbers.distance(life['pos'], chunk['pos'])
	life['judged_chunks'][chunk_key]['score'] = _score
	logging.debug('%s judged chunk #%s with score %s' % (' '.join(life['name']), chunk_key, _score))

def judge_all_chunks(life):
	logging.warning('%s is judging all chunks.' % (' '.join(life['name'])))
	_stime = time.time()
	
	for chunk in CHUNK_MAP:
		judge_chunk(life, chunk)
	
	logging.warning('%s completed judging all chunks (took %s.)' % (' '.join(life['name']), time.time()-_stime))
