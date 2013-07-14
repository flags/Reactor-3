from globals import *

import life as lfe

import references
import weapons
import chunks
import combat
import groups
import stats
import brain
import raids
import sight
import camps
import jobs

import logging
import numbers
import random
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

def parse_raw_judgements(life, target_id):
	lfe.execute_raw(life, 'judge', 'trust', break_on_false=False, life_id=target_id) * 100
	if lfe.execute_raw(life, 'judge', 'break_trust', break_on_true=True, break_on_false=False, life_id=target_id):
		brain.knows_alife_by_id(life, target_id)['trust'] = numbers.clip(brain.knows_alife_by_id(life, target_id)['trust'], -1000, -1)

def is_target_dangerous(life, target_id):
	target = brain.knows_alife_by_id(life, target_id)
	
	if target['life']['dead']:
		return False
	
	if target['danger']:
		if can_trust(life, target_id):
			return False
		
		return True
	
	return False

def is_safe(life):
	if get_targets(life):
		return False
	
	return True

def get_trusted(life, visible=True, invert=False):
	_trusted = []
	
	for target in life['know'].values():
		if not can_trust(life, target['life']['id']) == invert:
			if visible and sight.can_see_target(life, target['life']['id']):
				continue
			
			_trusted.append(target['life']['id'])
	
	return _trusted

def get_untrusted(life, visible=True):
	return get_trusted(life, visible=visible, invert=True)

def get_targets(life, must_be_known=False, escaped_only=False):
	_targets = []
	_combat_targets = []
	
	#if life['camp'] and raids.camp_has_raid(life['camp']):
	#	_targets.extend(raids.get_raiders(life['camp']))

	for alife in life['know'].values():
		if alife['life']['id'] in _targets:
			continue
		
		#TODO: Secrecy
		if is_target_dangerous(life, alife['life']['id']):
			_combat_targets.append(alife['life']['id'])
	
	_passed_combat_targets = []
	for target in [brain.knows_alife_by_id(life, i) for i in _combat_targets]:
		if not escaped_only and (target['escaped'] or target['last_seen_time']>=10):
			continue
		elif escaped_only:
			_targets.append(target['life']['id'])
			continue
		
		#TODO: Maybe the job calls for us to engage this target?
		if jobs.alife_is_factor_of_any_job(target['life']):
			continue
		
		_passed_combat_targets.append(target['life']['id'])
	
	if escaped_only:
		return _targets
	
	brain.store_in_memory(life, 'combat_targets', _passed_combat_targets)
	_targets.extend(_passed_combat_targets)
	
	#for target in _targets:
	#	print 'TARGET:',type(target),len(_targets)
	
	if must_be_known:
		for _target in _targets[:]:
			if not brain.knows_alife_by_id(life, _target):
				_targets.remove(_target)
	
	return _targets

def get_nearest_threat(life):
	_target = {'target': None, 'score': 9999}

	#_combat_targets = brain.retrieve_from_memory(life, 'combat_targets')
	#if not _combat_targets:
	#	return False
	
	for target in [brain.knows_alife_by_id(life, t) for t in get_targets(life, must_be_known=True)]:
		_score = numbers.distance(life['pos'], target['last_seen_at'])
		
		if not _target['target'] or _score<_target['score']:
			_target['target'] = target['life']['id']
			_target['score'] = _score
	
	return _target['target']

def get_invisible_threats(life):
	return get_visible_threats(life, _inverse=True)

def get_visible_threats(life, _inverse=False):
	_targets = []
	
	for target in [LIFE[t] for t in get_targets(life, must_be_known=True)]:
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

def _calculate_impressions(life, target_id):
	_target = brain.knows_alife_by_id(life, target_id)
	
	for impression in _target['impressions']:
		for key in _target['impressions'][impression]['modifiers']:
			if not key in _target:
				raise Exception('Key \'%s\' not in target.' % key)
			
			_target[key] += _target['impressions'][impression]['modifiers'][key]

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
	
	parse_raw_judgements(life, target_id)
	_calculate_impressions(life, target_id)
	
	if not _old_fondness == target['fondness']:
		print '%s fondness in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_fondness, target['fondness'])

	if not _old_danger == target['danger']:
		print '%s danger in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_danger, target['danger'])
	
	if not _old_trust == target['trust']:
		print '%s trust in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_trust, target['trust'])

def get_influence(life, target_id, gist):
	_impression = brain.get_impression(life, target_id, gist)
	
	if _impression:
		if 'influence' in _impression['modifiers']:
			return _impression['modifiers']['influence']
	
	return 0

def judge_search_pos(life, pos):
	return lfe.execute_raw(life, 'search', 'judge', break_on_true=True, pos1=life['pos'], pos2=pos)

def judge_chunk(life, chunk_id, visited=False):
	chunk = CHUNK_MAP[chunk_id]
	_score = 0
	
	if not chunk_id in life['known_chunks']:
		life['known_chunks'][chunk_id] = {'last_visited': 0,
			'digest': chunk['digest']}
	
	_antisocial_mod = stats.get_antisocial_percentage(life)
	_group_size_max = stats.get_max_group_size(life)
	_trusted = 0
	for _target in life['know'].values():
		_is_here = False
		
		if chunks.position_is_in_chunk(_target['last_seen_at'], chunk_id) and not _target['life']['path']:
			_is_here = True
		elif not _target['last_seen_time'] and _target['life']['path'] and chunks.position_is_in_chunk(lfe.path_dest(_target['life']), chunk_id):
			_is_here = True
			
		if _is_here:
			if is_target_dangerous(life, _target['life']['id']):
				_score -= 10
			else:
				_trusted += _target['trust']*_antisocial_mod
			
			_score += get_influence(life, _target['life']['id'], 'follow')
			_score += get_influence(life, _target['life']['id'], 'talk')
	
	if stats.desires_interaction(life):
		if _trusted>_group_size_max:
			_score += _trusted*_antisocial_mod
		else:
			_score += _trusted
	
	if visited:
		life['known_chunks'][chunk_id]['last_visited'] = WORLD_INFO['ticks']
	
	for item in chunk['items']:
		_item = brain.remember_known_item(life, item)
		if _item:
			_score += _item['score']

	maps.refresh_chunk(chunk_id)
	life['known_chunks'][chunk_id]['score'] = _score
	
	return _score

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
	
	_known_chunks_of_camp = references.get_known_chunks_in_reference(life, camp)
	
	_current_population = 0
	_current_trust = 0
	for _target in life['know'].values():
		if not references.is_in_reference(_target['last_seen_at'], camp):
			continue
		
		_current_population += 1
		
		if can_trust(life, _target['life']['id']):
			_current_trust += _target['trust']
		else:
			_current_trust -= _target['danger']
	
	_percent_known = len(_known_chunks_of_camp)/float(len(camp))
	_known_camps = [c['reference'] for c in life['known_camps'].values()]
	
	if _current_population > stats.get_max_group_size(life):
		_score = _current_trust*stats.get_antisocial_percentage(life)
		print life['name'],'2CROWDED'
	else:
		_score = _current_trust
	
	_camp = camps.get_camp_via_reference(camp)
	if _camp:
		_score += judge_group(life, camps.get_controlling_group(_camp))
	
	if stats.desires_to_create_camp(life):
		_score += len(groups.get_group(life['group'])['members'])/2<=len(_known_chunks_of_camp)
	
	#TODO: Why does this cause a crash?
	#return int(round(_percent_known*10))
	#print 'camp score:',(len(camp)*_percent_known),_score,(len(camp)*_percent_known)*_score
	return (len(camp)*_percent_known)*_score

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
		if not brain.get_alife_flag(life, raider, 'combat_score'):
			judge(life, raider)
		
		if brain.get_alife_flag(life, raider, 'combat_score'):
			_score += _knows['flags']['combat_score']
	
	logging.debug('RAID: %s judged raid with score %s' % (' '.join(life['name']), _score))
	
	return _score

def judge_group(life, group_id):
	_score = 0
	for member in groups.get_group(group_id)['members']:
		_knows = brain.knows_alife_by_id(life, member)
		if not _knows:
			continue
		
		if can_trust(life, member):
			_score += _knows['trust']
		else:
			_score -= _knows['danger']
	
	return _score

def group_judge_group(group_id, target_group_id):
	_group1 = groups.get_group(group_id)
	_group2 = groups.get_group(target_group_id)
	
	_group1_combat = groups.get_combat_score(group_id)
	_group2_combat = groups.get_combat_score(target_group_id)
	
	if _group1_combat > _group2_combat:
		pass

def is_group_hostile(life, group_id):
	_group = groups.get_group(group_id)
	
	if judge_group(life, group_id)>=0:
		return False
	
	return True

def believe_which_alife(life, alife):
	_scores = {}
	for ai in alife:
		_score = 0
		
		if can_trust(life, ai):
			_score = get_trust(life, ai)
		
		if _score in _scores:
			_scores[_score].append(ai)
		else:
			_scores[_score] = [ai]
	
	_winners = _scores[max(_scores)][:]
	
	if len(_winners)>1:
		_scores = {}
		for winner in _winners:
			_know = brain.knows_alife_by_id(life, winner)
			_score = _know['danger']
			
			if _score in _scores:
				_scores[_score].append(winner)
			else:
				_scores[_score] = [winner]
		
		return random.choice(_scores[max(_scores)])
	else:
		return _winners[0]
