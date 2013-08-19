from globals import WORLD_INFO, SETTINGS, MAP_SIZE

import life as lfe

import references
import weapons
import numbers
import combat
import speech
import chunks
import sight
import brain
import maps
import jobs

import random

def score_search(life,target,pos):
	return -numbers.distance(life['pos'],pos)

def score_shootcover(life,target,pos):
	if sight.view_blocked_by_life(life, target['life']['pos'], allow=[target['life']['id']]):
		return 9999
	
	return numbers.distance(life['pos'],pos)

def score_escape(life,target,pos):
	_target_distance_to_pos = numbers.distance(target['last_seen_at'], pos)
	_score = numbers.distance(life['pos'],pos)
	_score += 30-_target_distance_to_pos
	
	if not sight.can_see_position(target['life'], pos, distance=False):
		_score -= _target_distance_to_pos
	
	if not sight.can_see_position(target['life'], pos, distance=False):
		_score += _target_distance_to_pos/2
	
	return _score

def score_hide(life,target,pos):
	_chunk_id = '%s,%s' % ((pos[0]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'], (pos[1]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'])
	_chunk = maps.get_chunk(_chunk_id)
	_life_dist = numbers.distance(life['pos'], pos)
	_target_dist = numbers.distance(target['last_seen_at'], pos)
	
	#if sight.can_see_position(life, pos, distance=False):
	#	return 20-_target_dist
	
	if chunks.position_is_in_chunk(target['last_seen_at'], _chunk_id):
		return numbers.clip(300-_life_dist, 200, 300)
	
	if _chunk['reference'] and references.is_in_reference(target['last_seen_at'], _chunk['reference']):
		return numbers.clip(200-_life_dist, 100, 200)
	
	#if _chunk['type'] == 'building':
	#	if not sight._can_see_position(life['pos'], pos):
	#		print 'CLOSE!'
	#		return numbers.clip(49-_life_dist, 21, 49)
	#	
	#	print 'building'
	#	return 89-_life_dist
	if not sight._can_see_position(life['pos'], pos):
		return 99-_target_dist
	
	return 200

def position_for_combat(life,target,position,source_map):
	_cover = {'pos': None,'score': 9000}
	
	#TODO: Eventually this should be written into the pathfinding logic
	if sight.can_see_position(life, target['life']['pos']) and numbers.distance(life['pos'], target['life']['pos'])<=target['life']['engage_distance']:
		if not sight.view_blocked_by_life(life, target['life']['pos'], allow=[target['life']['id']]):
			lfe.clear_actions(life)
			return True
	
	#What can the target see?
	#TODO: Unchecked Cython flag
	_attack_from = sight.generate_los(life,target,position,source_map,score_shootcover,invert=True)
	
	if _attack_from:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _attack_from['pos']},200)
		return False
	
	return True

def travel_to_position(life, pos, stop_on_sight=False):
	if stop_on_sight and sight.can_see_position(life, pos):
		return False
	
	if not numbers.distance(life['pos'], pos):
		return False
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': (pos[0],pos[1])},200)
	
	return True

def search_for_target(life, target_id):
	#TODO: Variable size instead of hardcoded
	_know = brain.knows_alife_by_id(life, target_id)
	
	_size = 30
	if brain.alife_has_flag(life, target_id, 'search_map'):
		_search_map = brain.get_alife_flag(life, target_id, 'search_map')
	else:
		_search_map = maps.create_search_map(life, _know['last_seen_at'], _size)
		brain.flag_alife(life, target_id, 'search_map', value=_search_map)
	
	_lowest = {'score': -1, 'pos': None}
	_x_top_left = numbers.clip(_know['last_seen_at'][0]-(_size/2), 0, MAP_SIZE[0])
	_y_top_left = numbers.clip(_know['last_seen_at'][1]-(_size/2), 0, MAP_SIZE[1])
	
	for x in range(0, _size):
		_x = _x_top_left+x
		
		if _x >= MAP_SIZE[0]-1:
			continue
		
		for y in range(0, _size):
			_y = _y_top_left+y
			
			if _y >= MAP_SIZE[1]-1:
				continue
			
			if not _search_map[y, x]:
				continue
			
			if sight.can_see_position(life, (_x, _y)):
				_search_map[y, x] = 0
			
			if _search_map[y, x]>0 and (not _lowest['pos'] or _search_map[y, x] <= _lowest['score']):
				_lowest['score'] = _search_map[y, x]
				_lowest['pos'] = (_x, _y, x, y)
			#_search.append((_x, _y, x, y))

	if _lowest['pos']:
		x, y, _x, _y = _lowest['pos']
		
		if not travel_to_position(life, (x, y, _know['last_seen_at'][2]), stop_on_sight=True):
			_search_map[_y, _x] = 0
	else:
		_know['escaped'] = 2

def explore(life,source_map):
	#This is a bit different than the logic used for the other pathfinding functions
	pass

def escape(life, target, source_map):
	#With this function we're trying to get away from the target.
	#You'll see in `score_escape` that we're not trying to find full cover, but instead
	#just finding a way to get behind *something*.
	#
	_escape = sight.generate_los(life, target, target['last_seen_at'], source_map, score_escape)
	
	if _escape:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _escape['pos']},200)
		return False
	else:
		if brain.get_flag(life, 'scared') and not speech.has_considered(life, target, 'surrendered_to'):
			speech.communicate(life, 'surrender', target=target)
			brain.flag(life, 'surrendered')
			#print 'surrender'
	
	if lfe.path_dest(life):
		return True
	
	return True

def hide(life, target_id):
	_target = brain.knows_alife_by_id(life, target_id)
	_cover = sight.generate_los(life, _target, _target['last_seen_at'], WORLD_INFO['map'], score_hide, ignore_starting=True)
	
	if _cover:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _cover['pos']},200)		
		return False
	
	return True

def handle_hide(life,target,source_map):
	_weapon = combat.get_best_weapon(life)	
	_feed = None
	
	if _weapon:
		_feed = weapons.get_feed(_weapon['weapon'])		
	
	#TODO: Can we merge this into get_best_weapon()?
	_has_loaded_ammo = False
	if _feed:
		if _feed['rounds']:
			_has_loaded_ammo = True
	
	if _weapon and _weapon['weapon'] and (_weapon['rounds'] or _has_loaded_ammo):
		return escape(life,target,source_map)
	elif not _weapon and sight.find_known_items(life,matches={'type': 'weapon'},visible=True):
		return collect_nearby_wanted_items(life)
	else:
		return escape(life,target,source_map)

def collect_nearby_wanted_items(life, visible=True, matches={'type': 'gun'}):
	_highest = {'item': None,'score': -100000}
	_nearby = sight.find_known_items(life, matches=matches, visible=visible)
	
	for item in _nearby:
		_score = item['score']
		_score -= numbers.distance(life['pos'], item['item']['pos'])
		
		if not _highest['item'] or _score > _highest['score']:
			_highest['score'] = _score
			_highest['item'] = item['item']
	
	if not _highest['item']:
		return True
	
	_empty_hand = lfe.get_open_hands(life)
	
	if not _empty_hand:
		print 'No open hands, managing....'
		
		return False
	
	if life['pos'] == _highest['item']['pos']:
		lfe.clear_actions(life)
		
		for action in lfe.find_action(life, matches=[{'action': 'pickupholditem'}]):
			#print 'I was picking up something else...',_highest['item']['name']
			return False
		
		lfe.add_action(life,{'action': 'pickupholditem',
			'item': _highest['item'],
			'hand': random.choice(_empty_hand)},
			200,
			delay=lfe.get_item_access_time(life, _highest['item']))
		lfe.lock_item(life, _highest['item']['uid'])
	else:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _highest['item']['pos'][:2]},200)
	
	return False

def _find_alife(life, target, distance=-1):
	#Almost a 100% chance we know who this person is...
	_target = brain.knows_alife_by_id(life, target)
	
	#We'll try last_seen_at first
	#TODO: In the future we should consider how long it's been since we've seen them
	lfe.clear_actions(life)
	lfe.add_action(life, {'action': 'move','to': _target['last_seen_at'][:2]}, 900)
	
	if sight.can_see_position(life, _target['life']['pos']):
		if distance == -1 or numbers.distance(life['pos'], _target['last_seen_at'])<=distance:
			return True
	
	return False

def find_alife(life):
	if _find_alife(life, jobs.get_job_detail(life['job'], 'target')):
		lfe.stop(life)
		return True
	
	return False

#def find_alife_with_answer(life):
	#_asked = jobs.get_job_detail(life['job'], 'asked')
	
	#for target in life['know']:
	#	if target in _asked:
	#		continue
	#	
	#	if _find_alife(life, target):
	#		#_question = lfe.get_memory_via_id(life, jobs.get_job_detail(life['job'], 'question id'))
	#		print life['name'],'SHOULD BE ASKING TARGET',_asked
	#		_asked.append(target)
	#	else:
	#		print life['name'],'STILL LOOKING FOR TARGET!!!!!!!',_asked
	#		break
	#
	#print jobs.get_job_detail(life['job'], 'question id')
	#if lfe.get_memory_via_id(life, jobs.get_job_detail(life['job'], 'question id'))['answered']:
	#	return True
	#
	#return False

def follow_alife(life):
	if _find_alife(life, jobs.get_job_detail(life['job'], 'target'), distance=7):
		lfe.stop(life)
		return True
	
	return False

def _find_alife_and_say(life, target_id, say):
	_target = brain.knows_alife_by_id(life, target_id)
	
	if _find_alife(life, _target['life']['id']):
		speech.communicate(life, _say['gist'], matches=[{'id': _target['life']['id']}], **say)
		lfe.memory(life,
			'told about founder',
			camp=_say['camp'],
			target=_target['life']['id'])
		return True
	
	return False

#TODO: Put this in a new file
def find_alife_and_say(life):	
	return _find_alife_and_say(life, jobs.get_job_detail(life['job'], 'target'), jobs.get_job_detail(life['job'], 'target'))

def raid(life):
	jobs.add_job_candidate(_j, life)
	jobs.announce_job(life, _j)
	jobs.process_job(_j)
