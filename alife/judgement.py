from globals import *

import life as lfe

import weapons
import chunks
import combat
import brain

import logging
import numbers
import maps
import time

def judge_item(life, item):
	_score = 0
	
	if brain.get_flag(life, 'no_weapon') and item['type'] == 'gun':
		_score += 30
	elif brain.get_flag(life, 'no_backpack') and item['type'] == 'backpack':
		_score += 30
	
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

def knows_alife(life, alife):
	if alife['id'] in life['know']:
		return life['know'][alife['id']]
	
	return False

def judge_chunk(life, chunk_id, long=False, visited=False):
	chunk = CHUNK_MAP[chunk_id]
	
	if long:
		_max_score = SETTINGS['chunk size']*6
		_distance = (numbers.distance(life['pos'], chunk['pos'])/float(SETTINGS['chunk size']))
	else:
		_max_score = SETTINGS['chunk size']*4
		_distance = 0
	
	_initial = False
	if not chunk_id in life['known_chunks']:
		life['known_chunks'][chunk_id] = {'last_visited': 0,
			'digest': chunk['digest']}
		_initial = True
	
	_score = numbers.clip(_max_score-_distance, 0, _max_score)
	for _life in [LIFE[i] for i in LIFE]:
		if _life == life:
			continue
		
		if chunks.is_in_chunk(_life, chunk_id):
			if _life['id'] in life['know']:
				_score += lfe.get_known_life(life, _life['id'])['score']*.5
	
	if visited:
		life['known_chunks'][chunk_id]['last_visited'] = WORLD_INFO['ticks']
	
	if long:
		_score += len(chunk['items'])
	else:
		for item in chunk['items']:
			_item = brain.remember_known_item(life, item)
			if _item:
				_score += _item['score']
	
	maps.refresh_chunk(chunk_id)
	life['known_chunks'][chunk_id]['score'] = _score
	
	#if _initial:
	#	logging.debug('%s judged chunk #%s with score %s' % (' '.join(life['name']), chunk_id, _score))

def judge_all_chunks(life):
	logging.warning('%s is judging all chunks.' % (' '.join(life['name'])))
	_stime = time.time()
	
	for chunk in CHUNK_MAP:
		judge_chunk(life, chunk)
	
	logging.warning('%s completed judging all chunks (took %s.)' % (' '.join(life['name']), time.time()-_stime))

def judge_reference(life, reference, reference_type):
	#TODO: Length
	_score = 0
	_closest_chunk_key = {'key': None, 'distance': -1}
	
	for key in reference:
		_chunk = maps.get_chunk(key)
		_chunk_center = (_chunk['pos'][0]+(SETTINGS['chunk size']/2),
			_chunk['pos'][1]+(SETTINGS['chunk size']/2))
		_distance = numbers.distance(life['pos'], _chunk_center)
		
		if not _closest_chunk_key['key'] or _distance<_closest_chunk_key['distance']:
			_closest_chunk_key['key'] = key
			_closest_chunk_key['distance'] = _distance
		
		#Judge: ALife
		for ai in _chunk['life']:
			if ai == life['id']:
				continue
			
			if not lfe.can_see(life, LIFE[ai]['pos']):
				continue
			
			_knows = knows_alife(life, LIFE[ai])
			if not _knows:
				continue
				
			_score += _knows['score']
		
		#How long since we've been here?
		#if key in life['known_chunks']:
		#	_last_visit = numbers.clip(abs((life['known_chunks'][key]['last_visited']-WORLD_INFO['ticks'])/FPS), 2, 99999)
		#	_score += _last_visit
		#else:
		#	_score += WORLD_INFO['ticks']/FPS
		
	#Take length into account
	_score += len(reference)
	
	#Subtract distance in chunks
	_score -= _closest_chunk_key['distance']/SETTINGS['chunk size']
	
	#TODO: Average time since last visit (check every key in reference)
	#TODO: For tracking last visit use world ticks
	
	return _score
