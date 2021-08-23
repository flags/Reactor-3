from globals import *

import life as lfe

from . import references
from . import factions
import weapons
from . import chunks
from . import combat
from . import groups
import zones
from . import stats
from . import brain
from . import raids
from . import sight
from . import camps
import logic
from . import jobs

import logging
import bad_numbers
import random
import maps
import time

def judge_item(life, item_uid, initial=False):
	_item = ITEMS[item_uid]
	_score = 0
	
	if brain.get_flag(life, 'no_weapon') or item_uid in combat.get_equipped_weapons(life):
		if _item['type'] == 'gun':
			if combat.weapon_is_working(life, item_uid):
				_score += _item['accuracy']
			else:
				_score += _item['accuracy']*.5
		
		if _item['type'] in ['magazine', 'clip']:
			_score += 1
	
	if not initial:
		brain.get_remembered_item(life, item_uid)['score'] = _score
	
	return _score

def _get_highest_scoring_item(life):
	_highest = {'score': 0, 'uid': -1}
	for item_uid in life['inventory']:
		_score = judge_item(life, item_uid)
	
		if _highest['uid'] == -1 or _score>_highest['score']:
			_highest['uid'] = item_uid
			_highest['score'] = _score
	
	return _highest

def get_highest_scoring_item(life):
	return _get_highest_scoring_item(life)['uid']

def get_score_of_highest_scoring_item(life):
	return _get_highest_scoring_item(life)['score']

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

def get_ranged_combat_ready_score(life, consider_target_id=None):
	_score = 0
	
	if consider_target_id:
		_target = brain.knows_alife_by_id(life, consider_target_id)
		#TODO: Judge proper distance based on weapon equip time
		if bad_numbers.distance(life['pos'], _target['last_seen_at'])<sight.get_vision(life)//2:
			if lfe.get_held_items(life, matches=[{'type': 'gun'}]):
				_score += 1
		elif lfe.get_all_inventory_items(life, matches=[{'type': 'gun'}]):
			_score += 1
	
	return _score

def get_ranged_combat_rating_of_target(life, life_id, inventory_check=True):
	target = LIFE[life_id]
	_score = 1
	_score_mod = 1
	
	_items = [ITEMS[i] for i in lfe.get_all_visible_items(target) if i in ITEMS and logic.matches(ITEMS[i], {'type': 'gun'})]
	
	if not _items and inventory_check:
		_items = [i for i in lfe.get_all_inventory_items(target) if i['uid'] in ITEMS and logic.matches(i, {'type': 'gun'})]
		_score_mod = .5
	
	for item in _items:
		if bad_numbers.distance(life['pos'], target['pos']) > combat.get_engage_distance(target):
			_score += item['accuracy']//2
		else:
			_score += item['accuracy']
	
	if _score:
		_score += 2*(life['stats']['firearms']/10.0)
	
	return _score*_score_mod

def get_ranged_combat_rating_of_self(life):
	return get_ranged_combat_rating_of_target(life, life['id'])

def _calculate_trust(life, target_id):
	_knows = brain.knows_alife_by_id(life, target_id)
	_hard_trust = 0
	_soft_trust = 0
	
	if life['group'] and groups.is_member(life, life['group'], target_id):
		_hard_trust += 1
	
	for memory in lfe.get_memory(life, matches={'target': target_id, 'trust': '*'}):
		_soft_trust += memory['trust']
	
	_total_trust = _hard_trust+_soft_trust	
	
	if _hard_trust:
		_total_trust = bad_numbers.clip(_total_trust, _hard_trust, 10)
	
	return _total_trust

def get_trust(life, target_id):
	_knows = brain.knows_alife_by_id(life, target_id)
	
	return _knows['trust']

def can_trust(life, life_id):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	if not _knows:
		return False
	
	if _knows['alignment'] in ['trust', 'feign_trust']:
		return True
	
	if _knows['alignment'] == 'aggressive':
		return False
	
	#if _knows['trust']>=life['stats']['trustiness']:
	#	return True
	
	return False

def get_target_state(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	_mods = []
	
	if _target['asleep']:
		_mods.append('s')
	elif LIFE[life_id]['state_tier'] >= TIER_COMBAT:
		_mods.append('!')
	elif LIFE[life_id]['state_tier'] < TIER_COMBAT:
		_mods.append('c')
	
	return ''.join(_mods)

def get_tension(life):
	return brain.retrieve_from_memory(life, 'tension')

def get_tension_with(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	
	if _target['alignment'] in ['trust', 'feign_trust'] or not _target['last_seen_at']:
		return 0
	
	if not _target['last_seen_time'] and _target['dead']:
		return 0
	
	_distance = bad_numbers.clip(bad_numbers.distance(life['pos'], _target['last_seen_at']), 0, sight.get_vision(life))
	_tension = get_ranged_combat_rating_of_target(life, life_id)/float(get_ranged_combat_rating_of_self(life))
	
	return abs(((sight.get_vision(life)-_distance)/float(sight.get_vision(life)))*_tension)*(100-bad_numbers.clip(_target['last_seen_time'], 0, 100))/100.0

def get_max_tension_with(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	
	if _target['alignment'] == 'trust' or not _target['last_seen_at']:
		return 0
	
	if _target['alignment'] == 'feign_trust':
		return .85
	
	if _target['alignment'] in ['hostile', 'scared']:
		return 1
	
	return .75

def parse_raw_judgements(life, target_id):
	lfe.execute_raw(life, 'judge', 'trust', break_on_false=False, life_id=target_id)
	
	if lfe.execute_raw(life, 'judge', 'break_trust', life_id=target_id):
		brain.knows_alife_by_id(life, target_id)['trust'] = bad_numbers.clip(brain.knows_alife_by_id(life, target_id)['trust'], -1000, -1)
		return True
	
	return False

def is_target_dangerous(life, target_id):
	target = brain.knows_alife_by_id(life, target_id)
	
	if target['dead']:
		return False
	
	if target['alignment'] == 'trust':
		return False
	
	if target['alignment'] == 'hostile':
		return True
	
	return False

def is_target_threat(life, target_id):
	if lfe.execute_raw(life, 'judge', 'is_threat_if', life_id=target_id):
		return True
	
	return False

def track_target(life, target_id):
	_tracking = brain.get_flag(life, 'tracking_targets')
	
	if not _tracking:
		brain.flag(life, 'tracking_targets', [target_id])
		
		return None
	
	_tracking.append(target_id)

def untrack_target(life, target_id):
	_tracking = brain.get_flag(life, 'tracking_targets')
	
	if target_id in _tracking:
		_tracking.remove(target_id)

def is_tracking(life, target_id):
	_targets = brain.get_flag(life, 'tracking_targets')

	if not _targets:
		return False
	
	return target_id in _targets

def _get_target_value(life, life_id, value):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	return _knows[value]

def is_target_awake(life, life_id):
	return not _get_target_value(life, life_id, 'asleep')

def is_target_dead(life, life_id):
	return _get_target_value(life, life_id, 'dead')

def is_target_lost(life, target_id):
	_know = brain.knows_alife_by_id(life, target_id)
	if sight.can_see_position(life, _know['last_seen_at']):
		if sight.can_see_position(life, _know['life']['pos']):
			return False
		else:
			return True
	
	return False

def is_safe(life):
	if get_combat_targets(life, recent_only=True):
		return False
	
	return True

def is_scared(life):
	for target in get_all_visible_life(life):
		_knows = brain.knows_alife_by_id(life, target)
		
		if not _knows:
			continue
		
		if _knows['alignment'] == 'scared' and not _knows['asleep'] and not _knows['dead']:
			print(life['name'], 'is scared')
			return True
	
	return False

def get_trusted(life, visible=True, only_recent=False):
	_trusted = []
	
	for target in list(life['know'].values()):
		if can_trust(life, target['life']['id']):
			if only_recent and target['last_seen_time']>=150:
				continue
			
			if visible and not sight.can_see_target(life, target['life']['id']):
				continue
			
			_trusted.append(target['life']['id'])
	
	return _trusted

def judge(life):
	_threats = []
	_combat_targets = []
	_neutral_targets = []
	_tension = 0
	
	for alife_id in life['know']:
		_target = life['know'][alife_id]
		
		if _target['escaped'] == 2 or _target['dead'] or not _target['last_seen_at']:
			continue
		
		#TODO: Unhardcode 1. Can be used for reaction times
		if _target['last_seen_time'] >= 1 and not _target['escaped']:
			#TODO: Unhardcode 2000. How long to wait until a target is lost
			if _target['last_seen_time'] >= 2000:
				_target['escaped'] = 2
				logging.debug('%s flagged %s as lost (state 2).' % (' '.join(life['name']), ' '.join(_target['life']['name'])))
			elif _target['last_seen_time']>=25 and not _target['escaped']:
				_target['escaped'] = 1
		
		_tension += get_tension_with(life, alife_id)
		
		if can_trust(life, alife_id):
			_neutral_targets.append(alife_id)
		else:
			_combat_targets.append(alife_id)
			_threats.append(alife_id)
	
	brain.store_in_memory(life, 'threats', _threats)
	brain.store_in_memory(life, 'combat_targets', _combat_targets)
	brain.store_in_memory(life, 'targets', _neutral_targets)
	brain.store_in_memory(life, 'tension_spike', _tension-get_tension(life))
	brain.store_in_memory(life, 'tension', _tension)

def _target_filter(life, target_list, escaped_only, ignore_escaped, recent_only=False, ignore_lost=False, limit_distance=-1, filter_func=None):
	if not target_list:
		return []
	
	_return_targets = []
	
	for target in target_list:
		if LIFE[target]['dead']:
			continue
		
		_knows = brain.knows_alife_by_id(life, target)
		
		if (escaped_only and not _knows['escaped']==1) or (ignore_escaped and _knows['escaped']>=ignore_escaped):
			continue
		
		if ignore_lost and _knows['escaped'] == 2:
			continue
		
		if recent_only and _knows['last_seen_time'] >= 95:
			continue
		
		if not limit_distance == -1 and _knows['last_seen_at'] and bad_numbers.distance(life['pos'], _knows['last_seen_at'])>limit_distance:
			continue
		
		if filter_func and not filter_func(life, target):
			continue
	
		_return_targets.append(target)
	
	return _return_targets
	
def get_targets(life, escaped_only=False, ignore_escaped=True, limit_distance=-1, filter_func=None):
	return _target_filter(life, brain.retrieve_from_memory(life, 'targets'), escaped_only, ignore_escaped, limit_distance=limit_distance, filter_func=filter_func)

def get_combat_targets(life, escaped_only=False, ignore_escaped=False, ignore_lost=True, recent_only=False, limit_distance=-1, filter_func=None):
	return _target_filter(life, brain.retrieve_from_memory(life, 'combat_targets'), escaped_only, ignore_escaped, recent_only=recent_only, ignore_lost=ignore_lost, limit_distance=limit_distance, filter_func=filter_func)

def get_ready_combat_targets(life, escaped_only=False, ignore_escaped=False, recent_only=False, limit_distance=-1, filter_func=None):
	_targets = _target_filter(life, brain.retrieve_from_memory(life, 'combat_targets'), escaped_only, ignore_escaped, recent_only=recent_only, limit_distance=limit_distance, filter_func=filter_func)
	
	return [t for t in _targets if target_is_combat_ready(life, t)]

def get_threats(life, escaped_only=False, ignore_lost=True, ignore_escaped=True, recent_only=False, limit_distance=-1, filter_func=None):
	return _target_filter(life, brain.retrieve_from_memory(life, 'threats'), escaped_only, ignore_escaped, ignore_lost=ignore_lost, recent_only=recent_only, limit_distance=limit_distance, filter_func=filter_func)

def get_target_to_follow(life):
	_highest = {'id': 0, 'score': 0}
	
	for target_id in get_trusted(life, visible=False, only_recent=False):
		if not lfe.execute_raw(life, 'follow', 'follow_target_if', life_id=target_id):
			continue
		
		_score = 0
		_known_target = brain.knows_alife_by_id(life, target_id)
		
		if not _known_target['last_seen_at']:
			continue
		
		if _known_target['escaped'] == 2:
			continue
		
		#_score += _known_target['trust']
			
		if life['group'] and groups.is_leader(life, life['group'], target_id) and groups.get_stage(life, life['group']) == STAGE_RAIDING:
			_score += 1
	
		if _score > _highest['score']:
			_highest['id'] = target_id
			_highest['score'] = _score
	
	return _highest['id']

def get_target_to_guard(life):
	for target_id in get_targets(life):
		if not lfe.execute_raw(life, 'guard', 'guard_target_if', life_id=target_id):
			continue
		
		return target_id
	
	return 0

def get_nearest_threat(life):
	_target = {'target': 0, 'score': 9999}

	#_combat_targets = brain.retrieve_from_memory(life, 'combat_targets')
	#if not _combat_targets:
	#	return False
	
	for target in [brain.knows_alife_by_id(life, t) for t in get_combat_targets(life)]:
		_score = bad_numbers.distance(life['pos'], target['last_seen_at'])
		
		if not _target['target'] or _score<_target['score']:
			_target['target'] = target['life']['id']
			_target['score'] = _score
	
	return _target['target']

def get_visible_targets_in_list(life, targets):
	_visible_targets = get_visible_threats(life)
	_targets = []
	
	for target in targets:
		if target in _visible_targets:
			_targets.append(target)
	
	return _targets

def get_all_visible_life(life):
	return life['seen']

def get_invisible_threats(life):
	return get_visible_threats(life, _inverse=True)

def get_visible_threats(life, _inverse=False):
	_targets = []
	
	if not life['seen']:
		return []
	
	for target_id in get_threats(life):
		if not target_id in life['seen'] == _inverse:
			_targets.append(target_id)
	
	return _targets

def get_distance_to_target(life, target_id):
	target = brain.knows_alife_by_id(life, target_id)
	_goals = [target['last_seen_at']]
	_zones = [zones.get_zone_at_coords(target['last_seen_at'])]
	
	_zone = zones.get_zone_at_coords(life['pos'])
	if not _zone in _zones:
		_zones.append(_zone)
	
	return zones.dijkstra_map(life['pos'], _goals, _zones, return_score=True)

def get_nearest_target_in_list(life, target_list):
	_nearest_target = {'distance': 9999, 'target_id': None}

	for target_id in target_list:
		if not brain.knows_alife_by_id(life, target_id)['last_seen_at']:
			continue
		
		_distance = get_distance_to_target(life, target_id)
		
		if _distance < _nearest_target['distance'] or not _nearest_target['target_id']:
			_nearest_target['distance'] = _distance
			_nearest_target['target_id'] = target_id
	
	return _nearest_target

def get_nearest_combat_target(life):
	return get_nearest_target_in_list(life, get_combat_targets(life, ignore_lost=True, limit_distance=sight.get_vision(life)))

def get_nearest_trusted_target(life):
	return get_nearest_target_in_list(life, get_trusted(life))

def target_is_combat_ready(life, life_id):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	#They could be in those states but still have a weapon
	if _knows['last_seen_time']:# or _knows['state'] in ['surrender', 'hiding', 'hidden'] or _knows['asleep']:
		return False
	
	if combat.get_equipped_weapons(LIFE[life_id]):
		return True
	
	return False

def _calculate_danger(life, target):	
	_danger = 0	
	
	for memory in lfe.get_memory(life, matches={'target': target['life']['id'], 'danger': '*'}):
		_danger += memory['danger']
	
	return _danger

def judge_life(life, target_id):
	target = brain.knows_alife_by_id(life, target_id)
	
	_old_danger = target['danger']
	_old_trust = target['trust']
	
	target['danger'] = _calculate_danger(life, target)
	target['trust'] = _calculate_trust(life, target_id)
	
	parse_raw_judgements(life, target_id)

	#if not _old_danger == target['danger']:
	#	print '%s danger in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_danger, target['danger'])
	
	if not _old_trust == target['trust']:
		print('%s trust in %s: %s -> %s' % (' '.join(life['name']), ' '.join(target['life']['name']), _old_trust, target['trust']))

def judge_search_pos(life, pos):
	return lfe.execute_raw(life, 'search', 'judge', break_on_true=True, pos1=life['pos'], pos2=pos)

def judge_shelter(life, chunk_id):
	chunk = WORLD_INFO['chunk_map'][chunk_id]
	_known_chunk = life['known_chunks'][chunk_id]
	_score = 0
	
	if not chunk['type'] in ['building', 'town', 'outpost']:
		return 0
	
	if not chunks.get_flag(life, chunk_id, 'shelter'):
		_cover = []
		
		for pos in chunk['ground']:
			for z in range(life['pos'][2]+1, MAP_SIZE[2]):
				WORLD_INFO['map'][pos[0]][pos[1]][z]
				
				if WORLD_INFO['map'][pos[0]][pos[1]][z]:
					_cover.append(list(pos))
					
					break
		
		if not _cover:
			return 0
		
		chunks.flag(life, chunk_id, 'shelter_cover', _cover)
	
	chunks.flag(life, chunk_id, 'shelter', len(chunks.get_flag(life, chunk_id, 'shelter_cover')))
	
	return True

def judge_chunk_visually(life, chunk_id):
	if not chunk_id in life['known_chunks']:
		life['known_chunks'][chunk_id] = {'last_visited': -1,
			'last_seen': -1,
			'last_checked': -1,
			'discovered_at': WORLD_INFO['ticks'],
			'flags': {},
			'life': [],
			'score': 0}
	
	if lfe.ticker(life, 'judge_shelters', 5):
		if lfe.execute_raw(life, 'discover', 'remember_shelter'):
			judge_shelter(life, chunk_id)

def judge_chunk_life(life, chunk_id):
	if lfe.ticker(life, 'judge_chunk_life_tick', 30):
		return False
	
	_score = 0
	for life_id in life['known_chunks'][chunk_id]['life']:
		_target = brain.knows_alife_by_id(life, life_id)
		_is_here = False
		_actually_here = False
		
		if not _target['last_seen_at'] or not chunks.position_is_in_chunk(_target['last_seen_at'], chunk_id) and not _target['life']['path']:
			continue
	
	return _score 

def judge_chunk(life, chunk_id, visited=False, seen=False, checked=True, investigate=False):
	if lfe.ticker(life, 'judge_tick', 30):
		return False
	
	chunk = maps.get_chunk(chunk_id)
	_score = 0
	
	if not chunk_id in life['known_chunks']:
		life['known_chunks'][chunk_id] = {'last_visited': -1,
			'last_seen': -1,
			'last_checked': -1,
			'discovered_at': WORLD_INFO['ticks'],
			'flags': {},
			'life': []}
	
	_camp = chunks.get_global_flag(chunk_id, 'camp')
	if _camp and not _camp in life['known_camps']:
		camps.discover_camp(life, _camp)
	
	_known_chunk = life['known_chunks'][chunk_id]	
	
	if seen:
		_known_chunk['last_seen'] = WORLD_INFO['ticks']
	
	if visited:
		_known_chunk['last_visited'] = WORLD_INFO['ticks']
		_known_chunk['last_seen'] = WORLD_INFO['ticks']
	
	if checked:
		_known_chunk['last_checked'] = WORLD_INFO['ticks']
	
	_trusted = 0
	for _target in list(life['know'].values()):
		if not _target['last_seen_at']:
			continue
		
		_is_here = False
		_actually_here = False
		
		if chunks.position_is_in_chunk(_target['last_seen_at'], chunk_id) and not _target['life']['path']:
			_is_here = True
		elif not _target['last_seen_time'] and _target['life']['path'] and chunks.position_is_in_chunk(lfe.path_dest(_target['life']), chunk_id):
			_is_here = True
		
		if chunks.position_is_in_chunk(_target['life']['pos'], chunk_id):
			_actually_here = True
			
		if _is_here:
			if not _target['life']['id'] in _known_chunk['life']:
				_known_chunk['life'].append(_target['life']['id'])
			
			if is_target_dangerous(life, _target['life']['id']):
				_score -= 10
			elif life['group'] and groups.is_leader(life, life['group'], _target['life']['id']):
				_trusted += _target['trust']
		else:
			if _target['life']['id'] in _known_chunk['life']:
				_known_chunk['life'].remove(_target['life']['id'])
	
	if investigate and not visited:
		chunks.flag(life, chunk_id, 'investigate', True)
	elif visited and chunks.get_flag(life, chunk_id, 'investigate'):
		chunks.unflag(life, chunk_id, 'investigate')
	
	if chunks.get_flag(life, chunk_id, 'investigate'):
		_score += 5
	
	#for camp in life['known_camps']:
	#	if not chunk_id in camps.get_camp(camp)['reference']:
	#		continue
		
		
		#if not life['camp'] == camp['id']:
		#	continue
	
		#if stats.desires_shelter(life):
		#	_score += judge_camp(life, life['camp'])
	
	if lfe.execute_raw(life, 'discover', 'remember_shelter'):
		judge_shelter(life, chunk_id)
	
	#if stats.desires_interaction(life):
	#	_score += _trusted
	
	if seen:
		pass
		#TODO: Still a good idea... maybe use for shelter?
		#for item in chunk['items']:
		#	_item = brain.remember_known_item(life, item)
		#	if _item:
		#		_score += _item['score']

	life['known_chunks'][chunk_id]['score'] = _score
	
	return _score

def judge_all_chunks(life):
	logging.warning('%s is judging all chunks.' % (' '.join(life['name'])))
	_stime = time.time()
	
	for chunk in WORLD_INFO['chunk_map']:
		judge_chunk(life, chunk)
	
	logging.warning('%s completed judging all chunks (took %s.)' % (' '.join(life['name']), time.time()-_stime))

def judge_reference(life, reference_id, known_penalty=False):
	#TODO: Length
	_score = 0
	_count = 0
	_closest_chunk_key = {'key': None, 'distance': -1}
	
	for key in references.get_reference(reference_id):
		if known_penalty and key in life['known_chunks']:
			continue
		
		_count += 1
		_chunk = maps.get_chunk(key)
		_chunk_center = (_chunk['pos'][0]+(WORLD_INFO['chunk_size']//2),
			_chunk['pos'][1]+(WORLD_INFO['chunk_size']//2))
		_distance = bad_numbers.distance(life['pos'], _chunk_center)
		
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
		
		#How long since we've been here?
		#if key in life['known_chunks']:
		#	_last_visit = bad_numbers.clip(abs((life['known_chunks'][key]['last_visited']-WORLD_INFO['ticks'])//FPS), 2, 99999)
		#	_score += _last_visit
		#else:
		#	_score += WORLD_INFO['ticks']//FPS
		
	#Take length into account
	_score += _count
	
	#Subtract distance in chunks
	_score -= _closest_chunk_key['distance']//WORLD_INFO['chunk_size']
	
	#TODO: Average time since last visit (check every key in reference)
	#TODO: For tracking last visit use world ticks
	
	return _score

def judge_camp(life, camp, for_founding=False):
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
	
	#In addition to all that, we want to prevent returning camps that are too close
	#to other camps. This is hardcoded (can't think of a reason why the ALife would want this)
	
	if for_founding:
		for _known_camp in [c['reference'] for c in list(life['known_camps'].values())]:
			for _pos1 in _known_camp:
				pos1 = [int(i) for i in _pos1.split(',')]
				for _pos2 in camp:
					pos2 = [int(i) for i in _pos2.split(',')]
					_dist = bad_numbers.distance(pos1, pos2) // WORLD_INFO['chunk_size']
					
					if _dist <= 15:
						return 0
	
	_known_chunks_of_camp = references.get_known_chunks_in_reference(life, camp)
	
	_current_population = 0
	_current_trust = 0
	for _target in list(life['know'].values()):
		if not references.is_in_reference(_target['last_seen_at'], camp):
			continue
		
		_current_population += 1
		
		if can_trust(life, _target['life']['id']):
			_current_trust += _target['trust']
		else:
			_current_trust -= _target['danger']
	
	_percent_known = len(_known_chunks_of_camp)/float(len(camp))
	_score = _current_trust
	_camp = camps.get_camp_via_reference(camp)
	
	if _camp:
		_score += judge_group(life, camps.get_controlling_group(_camp))
	
	if stats.desires_to_create_camp(life):
		_score += len(groups.get_group(life, life['group'])['members'])//2<=len(_known_chunks_of_camp)
	
	#TODO: Why does this cause a crash?
	#return int(round(_percent_known*10))
	#print 'camp score:',(len(camp)*_percent_known),_score,(len(camp)*_percent_known)*_score
	return (len(camp)*_percent_known)*_score

def judge_jobs(life):
	_tier = 0
	
	if life['task']:
		return life['job']
	
	_new_job = None
	_old_job = life['job']
	#life['job'] = None
		
	for job in [jobs.get_job(j) for j in life['jobs']]:
		if not jobs.get_free_tasks(job['id']):
			continue
		
		if not jobs.meets_job_requirements(life, job['id']):
			continue
		
		if life['group'] and job['gist'] == 'create_group':
			if not stats.wants_to_abandon_group(life, life['group']):
				jobs.reject_job(job['id'], life['id'])
				continue
			
			if life['group'] == jobs.get_flag(job['id'], 'group'):
				jobs.reject_job(job['id'], life['id'])
				continue
		
		if jobs.has_completed_or_rejected_job(life, job['id']):
			continue
		
		if job['tier'] >= _tier:
			#jobs.join_job(job['id'], life['id'])
			_new_job = job['id']
			_tier = job['tier']
	
	if not _old_job == _new_job:
		if _old_job:
			jobs.leave_job(_old_job, life['id'])
	
		if _new_job:
			jobs.join_job(_new_job, life['id'])
	
	if life['job']:
		life['task'] = jobs.get_next_task(life, life['job'])
	
	if not life['task']:
		if life['job']:
			jobs.leave_job(life['job'], life['id'], reject=True)
	
	if not life['job'] == _old_job:
		life['completed_tasks'] = []
	
	return life['job']

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
			judge_life(life, raider)
		
		if brain.get_alife_flag(life, raider, 'combat_score'):
			_score += _knows['flags']['combat_score']
	
	logging.debug('RAID: %s judged raid with score %s' % (' '.join(life['name']), _score))
	
	return _score

def judge_group(life, group_id):
	_score = 0
	for member in groups.get_group(life, group_id)['members']:
		if member == life['id']:
			continue
		
		_knows = brain.knows_alife_by_id(life, member)
		if not _knows:
			continue
		
		if is_target_dangerous(life, member):
			_score += get_trust(life, member)
		else:
			_score += get_trust(life, member)
	
	return _score

def group_judge_group(life, group_id, target_group_id):
	_group1 = groups.get_group(life, group_id)
	_group2 = groups.get_group(life, target_group_id)
	
	_group1_combat = groups.get_combat_score(life, group_id)
	_group2_combat = groups.get_combat_score(life, target_group_id)
	
	if _group1_combat > _group2_combat:
		pass

def is_group_hostile(life, group_id):
	_group = groups.get_group(life, group_id)
	
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
	
	return _winners[0]

def get_best_goal(life):
	for goal in brain.retrieve_from_memory(life, 'active_goals'):
		return goal
	
	return -1

def get_known_shelters(life):
	return [chunk_id for chunk_id in life['known_chunks'] if chunks.get_flag(life, chunk_id, 'shelter')]

def get_best_shelter(life):
	_best_shelter = {'distance': -1, 'shelter': None}
	
	if life['group'] and groups.get_shelter(life, life['group']):
		_shelter = groups.get_shelter(life, life['group'])
		
		if _shelter:
			_nearest_chunk_key = references.find_nearest_key_in_reference(life, _shelter)
			_shelter_center = [int(val)+(WORLD_INFO['chunk_size']//2) for val in _nearest_chunk_key.split(',')]
			_dist = bad_numbers.distance(life['pos'], _shelter_center)
			
			judge_chunk(life, _nearest_chunk_key)
			
			if _dist <= logic.time_until_midnight()*life['speed_max']:
				print(life['name'],'can get to shelter in time')
				return _nearest_chunk_key
			else:
				print(life['name'],'cant get to shelter in time')
	
	for chunk_key in [chunk_id for chunk_id in life['known_chunks'] if chunks.get_flag(life, chunk_id, 'shelter')]:
		chunk_center = [int(val)+(WORLD_INFO['chunk_size']//2) for val in chunk_key.split(',')]
		_score = bad_numbers.distance(life['pos'], chunk_center)
		
		if not _best_shelter['shelter'] or _score<_best_shelter['distance']:
			_best_shelter['shelter'] = chunk_key
			_best_shelter['distance'] = _score
	
	return _best_shelter['shelter']

def update_camps(life):
	for camp in list(life['known_camps'].values()):
		camp['snapshot']['life'] = []
		camp['snapshot']['groups'] = {}
	
	for _target in list(life['know'].values()):
		if not _target['last_seen_at']:
			continue
		
		for camp in list(life['known_camps'].values()):
			if not camps.position_is_in_camp(_target['last_seen_at'], camp['id']):
				continue
			
			camp['snapshot']['life'].append(_target['life']['id'])
			if _target['life']['group']:
				if _target['life']['group'] in camp['snapshot']['groups']:
					camp['snapshot']['groups'][_target['life']['group']] += 1
				else:
					camp['snapshot']['groups'][_target['life']['group']] = 1
	
	#for camp in life['known_camps'].values():
	#	if not camp['snapshot']['life']:
	#		continue
	#	
	#	print life['name'], camp['id'], camp['snapshot']['life']