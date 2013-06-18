from globals import *

import life as lfe

import weapons
import chunks
import combat
import brain
import raids
import sight

import logging
import numbers
import maps
import time

def judge_item(life, item):
	_score = 0
	
	if brain.get_flag(life, 'no_weapon') and item['type'] == 'gun':
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

def get_combat_rating(life):
	_score = 0
	
	#TODO: CLose? Check equipped items only. Far away? Check inventory.
	if lfe.get_held_items(life, matches=[{'type': 'gun'}]) or lfe.get_all_inventory_items(life, matches=[{'type': 'gun'}]):
		_score += 10
	
	return _score

def get_trust(life, target_id):
	_knows = brain.knows_alife_by_id(life, target_id)
	_trust = 0
	
	for memory in lfe.get_memory(life, matches={'target': target_id, 'trust': '*'}):
		_trust += memory['trust']
	
	return _trust

def can_trust(life, target_id, low=0):
	_knows = brain.knows_alife_by_id(life, target_id)
	
	if _knows['trust']>=low:
		return True
	
	return False

def should_trust(life, target_id):
	#TODO: What is our minimum score for trust?
	return can_trust(life, target_id, low=1)

def is_target_dangerous(life, target_id):
	target = brain.knows_alife_by_id(life, target_id)
	
	if target['danger']:
		if can_trust(life, target_id):
			return False
		
		return True
	
	return False

def is_safe(life):
	if get_targets(life):
		return False
	
	return True

def get_talkable(life, secrecy=0):
	_talkable = []
	
	for alife in life['know'].values():
		#TODO: Secrecy
		if can_trust(life, alife['life']['id']):
			_talkable.append(alife['life']['id'])
	
	return _talkable

def get_targets(life):
	_targets = []
	
	if life['camp'] and raids.camp_has_raid(life['camp']):
		_targets.extend(raids.get_raiders(life['camp']))

	_combat_targets = brain.retrieve_from_memory(life, 'combat_targets')
	if _combat_targets:
		_targets.extend([c['who']['life']['id'] for c in _combat_targets])
	
	for alife in life['know'].values():
		if alife['life']['id'] in _targets:
			continue
		
		#TODO: Secrecy
		if is_target_dangerous(life, alife['life']['id']):
			_targets.append(alife['life']['id'])
	
	#_combat_targets = brain.retrieve_from_memory(life, 'combat_targets')
	#if _combat_targets:
	#	_targets.extend([t['who']['life']['id'] for t in _combat_targets if not t['who']['life']['id'] in _targets])
	
	return _targets

def get_nearest_threat(life):
	_target = {'target': None, 'score': 9999}

	#_combat_targets = brain.retrieve_from_memory(life, 'combat_targets')
	#if not _combat_targets:
	#	return False
	
	for target in [brain.knows_alife_by_id(life, t) for t in get_targets(life)]:
		_score = numbers.distance(life['pos'], target['last_seen_at'])
		
		if not _target['target'] or _score<_target['score']:
			_target['target'] = target['life']['id']
			_target['score'] = _score
	
	return _target['target']

def get_invisible_threats(life):
	return get_visible_threats(life, _inverse=True)

def get_visible_threats(life, _inverse=False):
	_targets = []
	
	for target in [LIFE[t] for t in get_targets(life)]:
		if not sight.can_see_target(life, target['id']) == _inverse:
			_targets.append(target['id'])
	
	return _targets

def get_fondness(life, target_id):
	target = brain.knows_alife_by_id(life, target_id)
	
	return target['fondness']

def _get_impressions(life, target):
	if WORLD_INFO['ticks']-target['met_at_time']<=50 and not brain.get_impression(life, target['life']['id'], 'had_weapon'):
		if lfe.get_held_items(target['life'], matches=[{'type': 'gun'}]):
			brain.add_impression(life, target['life']['id'], 'had_weapon', {'danger': 2})

def _calculate_impressions(life, target):
	for impression in target['impressions']:
		for key in target['impressions'][impression]['modifiers']:
			if not key in target:
				raise Exception('Key \'%s\' not in target.' % ' '.join(target['life']['name']))
			
			target[key] += target['impressions'][impression]['modifiers'][key]

def _calculate_fondness(life, target):
	_fondness = 0
	
	for memory in lfe.get_memory(life, matches={'target': target['life']['id']}):
		if memory['text'] == 'friendly':
			_fondness += 1
	
	return _fondness

def _calculate_danger(life, target):
	if target['life']['asleep']:
		return 0
	
	_danger = 0	
	
	for memory in lfe.get_memory(life, matches={'target': target['life']['id'], 'danger': '*'}):
		_danger += memory['danger']
	
	return _danger

def judge(life, target_id):
	target = brain.knows_alife_by_id(life, target_id)
	
	_old_fondness = target['fondness']
	_old_danger = target['danger']
	_old_trust = target['trust']
	
	_get_impressions(life, target)
	target['fondness'] = _calculate_fondness(life, target)
	target['danger'] = _calculate_danger(life, target)
	target['trust'] = get_trust(life, target_id)
	
	_calculate_impressions(life, target)
	
	if not _old_fondness == target['fondness']:
		print '%s fondness in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_fondness, target['fondness'])

	if not _old_danger == target['danger']:
		print '%s danger in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_danger, target['danger'])
	
	if not _old_trust == target['trust']:
		print '%s trust in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_trust, target['trust'])

def judge_old(life, target):
	_like = 0
	_dislike = 0
	_is_hostile = False
	_surrendered = False
	
	if target['life']['asleep']:
		return 0

	if 'greeting' in target['received']:
		_like += 1
	
	#if 'greeting' in target['sent']:
	#	_like += 1
	
	for memory in lfe.get_memory(life, matches={'target': target['life']['id']}):
		if memory['text'] == 'friendly':
			_like += 2
		
		elif memory['text'] == 'hostile':
			_is_hostile = True
			_dislike += 2
		
		elif memory['text'] == 'traitor':
			_is_hostile = True
			_dislike += 2
		
		elif memory['text'] == 'shot by':
			_is_hostile = True
			_dislike += 2
		
		elif memory['text'] == 'compliant':
			_like += 2
		
		elif memory['text'] == 'surrendered':
			_surrendered = True

	#First impressions go here
	if WORLD_INFO['ticks']-target['met_at_time']<=50 and not brain.get_impression(life, target['life'], 'had_weapon'):
		if lfe.get_held_items(target['life'], matches=[{'type': 'gun'}]):
			brain.add_impression(life, target['life'], 'had_weapon', {'danger': 2})
	
	if brain.get_impression(life, target['life'], 'had_weapon'):
		if not lfe.get_held_items(target['life'], matches=[{'type': 'gun'}]):
			_like += abs(target['impressions']['had_weapon']['score'])
	
	for impression in target['impressions']:
		_score = target['impressions'][impression]['score']
		
		if _score < 0:
			_dislike += abs(_score)
		else:
			_like += _score
	
	#TODO: What?
	#_like += brain.get_trust(life, target['life']['id'])
	
	if target['trust']<0 and not brain.can_trust(life, target['life']['id']):
		print 'DECLARING HOSTILE!!!'
		_is_hostile = True
	
	if _is_hostile:
		if _surrendered:
			target['flags']['surrendered'] = True
		else:
			_life_combat_score = get_combat_rating(life)
			_target_combat_score = get_combat_rating(target['life'])
			brain.flag_alife(life, target['life'], 'combat_score', value=_life_combat_score-_target_combat_score)
			
			logging.warning('** ALife combat scores for %s vs. %s: %s **' % (' '.join(life['name']), ' '.join(target['life']['name']), _life_combat_score-_target_combat_score))
			
			#if _target_combat_score>0:
			#	return -_target_combat_score
	
	if brain.can_trust(life, target['life']['id']):
		return _like-_dislike
	else:
		return -1

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
		if _life['id'] == life['id']:
			continue
		
		#if chunks.is_in_chunk(_life, chunk_id):
		#	if _life['id'] in life['know']:
		#		_score += lfe.get_known_life(life, _life['id'])['score']*.5
	
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
	
	return _score
	#if _initial:
	#	logging.debug('%s judged chunk #%s with score %s' % (' '.join(life['name']), chunk_id, _score))

def judge_all_chunks(life):
	logging.warning('%s is judging all chunks.' % (' '.join(life['name'])))
	_stime = time.time()
	
	for chunk in CHUNK_MAP:
		judge_chunk(life, chunk)
	
	logging.warning('%s completed judging all chunks (took %s.)' % (' '.join(life['name']), time.time()-_stime))

def judge_reference(life, reference, reference_type, known_penalty=False):
	#TODO: Length
	_score = 0
	_count = 0
	_closest_chunk_key = {'key': None, 'distance': -1}
	
	for key in reference:
		if known_penalty and key in life['known_chunks']:
			continue
		
		_count += 1
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
			
			if not sight.can_see_target(life, ai):
				continue
			
			_knows = brain.knows_alife(life, LIFE[ai])
			if not _knows:
				continue
				
			_score += get_fondness(life, ai)
		
		#How long since we've been here?
		#if key in life['known_chunks']:
		#	_last_visit = numbers.clip(abs((life['known_chunks'][key]['last_visited']-WORLD_INFO['ticks'])/FPS), 2, 99999)
		#	_score += _last_visit
		#else:
		#	_score += WORLD_INFO['ticks']/FPS
		
	#Take length into account
	_score += _count
	
	#Subtract distance in chunks
	_score -= _closest_chunk_key['distance']/SETTINGS['chunk size']
	
	#TODO: Average time since last visit (check every key in reference)
	#TODO: For tracking last visit use world ticks
	
	return _score

def judge_camp(life, camp):
	#This is kinda complicated so I'll do my best to describe what's happening.
	#The ALife keeps track of chunks it's aware of, which we'll use when
	#calculating how much of a camp we know about (value between 0..1)
	#First we score the camp based on what we DO know, which is pretty cut and dry:
	#
	#We consider:
	#	How big the camp is vs. how many people we think we're going to need to fit in it (not a factor ATM)
	#		A big camp won't be attractive to just one ALife, but a faction will love the idea of having a larger base
	#	Distance from other camps
	#		Certain ALife will prefer isolation
	#
	#After scoring this camp, we simply multiply by the percentage of the camp
	#that is known. This will encourage ALife to discover a camp first before
	#moving in.
	
	_bonus = 0
	_known_chunks_of_camp = []
	for _chunk_key in camp:
		if not _chunk_key in life['known_chunks']:
			continue
		
		_known_chunks_of_camp.append(_chunk_key)
	
	_percent_known = len(_known_chunks_of_camp)/float(len(camp))
	
	_known_camps = [c['reference'] for c in life['known_camps'].values()]
	#print _known_camps
	if camp in _known_camps:
		print 'ssssssssssssssssss'
	#print _known_camps
	#if lfe.get_memory(life, matches={'text': 'heard about camp', 'camp': camp}):
	#	_bonus += 2
	#	print 'bonus!!!!!!!!!'
	
	#TODO: Why does this cause a crash?
	#return int(round(_percent_known*10))
	return (len(camp)*_percent_known)+_bonus

def judge_job(life, job):
	_score = 0
	for factor in job['factors']:
		if factor['type'] == 'alife':
			_alife = brain.knows_alife_by_id(life, factor['value'])
			
			if not _alife:
				continue
			
			_score += judge(life, _alife)

	return _score

def judge_raid(life, raiders, camp):
	# score >= 0: We can handle it
	# 		<  0: We can't handle it 
	_score = 0
	for raider in raiders:
		_knows = brain.knows_alife_by_id(life, raider)
		if not _knows:
			#TODO: Confidence
			_score -= 2
			continue
		
		#TODO: Find a better way to do this
		#TODO: This has to be broken: _knows['life']
		if not brain.get_alife_flag(life, _knows['life'], 'combat_score'):
			judge(life, raider)
		
		if brain.get_alife_flag(life, _knows['life'], 'combat_score'):
			_score += _knows['flags']['combat_score']
	
	logging.debug('RAID: %s judged raid with score %s' % (' '.join(life['name']), _score))
	
	return _score

def believe_which_alife(life, alife):
	_scores = {}
	for ai in alife:
		_score = get_trust(life, ai)
		_scores[_score] = ai
	
	return _scores[max(_scores)]
		
