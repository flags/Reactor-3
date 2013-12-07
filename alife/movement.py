from globals import WORLD_INFO, SETTINGS, MAP_SIZE, ITEMS, LIFE

import life as lfe

import references
import weapons
import numbers
import combat
import speech
import chunks
import memory
import alife
import zones
import sight
import brain
import maps
import jobs

import random

def position_to_attack(life, target):
	_target_positions, _zones = combat.get_target_positions_and_zones(life, [target])
	_nearest_target_score = zones.dijkstra_map(life['pos'], _target_positions, _zones, return_score=True)
	
	#TODO: Short or long-range weapon?
	#if _nearest_target_score >= sight.get_vision(life)/2:
	if not sight.can_see_position(life, brain.knows_alife_by_id(life, target)['last_seen_at'], block_check=True, strict=True) or sight.view_blocked_by_life(life, _target_positions[0], allow=[target]):
		print life['name'], 'changing position for combat...', life['name'], LIFE[target]['name']
		
		_avoid_positions = []
		for life_id in life['seen']:
			if life_id == target or life['id'] == life_id:
				continue
			
			if alife.judgement.can_trust(life, life_id):
				_avoid_positions.append(lfe.path_dest(LIFE[life_id]))
			else:
				_avoid_positions.append(brain.knows_alife_by_id(life, life_id)['last_seen_at'])
		
		_cover = _target_positions
		
		_zones = []
		for pos in _cover:
			_zone = zones.get_zone_at_coords(pos)
			
			if not _zone in _zones:
				_zones.append(_zone)
		
		if not lfe.find_action(life, [{'action': 'dijkstra_move', 'orig_goals': _cover[:], 'avoid_positions': _avoid_positions}]):
			lfe.stop(life)
			lfe.add_action(life, {'action': 'dijkstra_move',
				                  'rolldown': True,
				                  'goals': _cover[:],
			                      'orig_goals': _cover[:],
			                      'avoid_positions': _avoid_positions,
			                      'reason': 'positioning for attack'},
				           999)
			
			return False
		else:
			return False
	elif life['path']:
		lfe.stop(life)
	
	return True

def travel_to_position(life, pos, stop_on_sight=False):
	if stop_on_sight and sight.can_see_position(life, pos):
		return True
	
	if not numbers.distance(life['pos'], pos):
		return True
	
	_dest = lfe.path_dest(life)
	if _dest and _dest[:2] == pos[:2]:
		return False
	
	lfe.clear_actions(life)
	lfe.add_action(life,{'action': 'move','to': (pos[0],pos[1])},200)
	
	return False

def search_for_target(life, target_id):
	#TODO: Variable size instead of hardcoded
	_know = brain.knows_alife_by_id(life, target_id)
	
	_size = 30
	if brain.alife_has_flag(life, target_id, 'search_map'):
		_search_map = brain.get_alife_flag(life, target_id, 'search_map')
	else:
		_search_map = maps.create_search_map(life, _know['last_seen_at'], _size)
		brain.flag_alife(life, target_id, 'search_map', value=_search_map)
		
		lfe.stop(life)
		lfe.walk_to(life, _know['last_seen_at'][:2])
	
	if life['path'] or lfe.find_action(life, matches=[{'action': 'move'}]):
		return False
	
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

	if _lowest['pos']:
		x, y, _x, _y = _lowest['pos']
		
		if travel_to_position(life, (x, y, _know['last_seen_at'][2]), stop_on_sight=True):
			_search_map[_y, _x] = 0
	else:
		_know['escaped'] = 2

def escape(life, targets):
	_target_positions = []
	_visible_target_chunks = []
	_zones = [zones.get_zone_at_coords(life['pos'])]
	
	for target_id in targets:
		_target = brain.knows_alife_by_id(life, target_id)
		_target_positions.append(_target['last_seen_at'][:])
		_zone = zones.get_zone_at_coords(_target['last_seen_at'])
		
		if not _zone in _zones:
			_zones.append(_zone)
		
		for chunk_key in chunks.get_visible_chunks_from(_target['last_seen_at'], sight.get_vision(_target['life'])):
			if chunk_key in _visible_target_chunks:
				continue
			
			_visible_target_chunks.append(chunk_key)
	
	for friendly_id in life['seen']:
		_chunk_key = lfe.get_current_chunk_id(LIFE[friendly_id])
		
		if not _chunk_key in _visible_target_chunks:
			_visible_target_chunks.append(_chunk_key)
	
	_cover_exposed_by = brain.get_flag(life, 'cover_exposed')
	if _cover_exposed_by and not _cover_exposed_by in life['seen']:
		brain.unflag(life, 'cover_exposed')
	
	if not _target_positions:
		return False
	
	#TODO: #combat: For lower limit in return_score_in_range, use range of weapon
	_cover = zones.dijkstra_map(life['pos'],
	                            _target_positions,
	                            _zones,
	                            avoid_chunks=_visible_target_chunks,
	                            return_score_in_range=[1, sight.get_vision(life)])
	_cover = [(c[0], c[1], life['pos'][2]) for c in _cover]
	if not _cover:
		return False
	
	_zones = [zones.get_zone_at_coords(life['pos'])]
	for _pos in _cover:
		_zone = zones.get_zone_at_coords(_pos)
		
		if not _zone in _zones:
			_zones.append(_zone)
	
	if lfe.find_action(life, [{'action': 'dijkstra_move', 'goals': _cover[:]}]):
		return True
	
	lfe.stop(life)
	lfe.add_action(life, {'action': 'dijkstra_move',
	                      'rolldown': True,
	                      'zones': _zones,
	                      'goals': _cover[:],
	                      'reason': 'escaping'},
	               999)

def collect_nearby_wanted_items(life, only_visible=True, matches={'type': 'gun'}):
	_highest = {'item': None,'score': -100000}
	_nearby = sight.find_known_items(life, matches=matches, only_visible=only_visible)
	
	for item in _nearby:
		_item = brain.get_remembered_item(life, item)
		_score = _item['score']
		_score -= numbers.distance(life['pos'], ITEMS[item]['pos'])
		
		if not _highest['item'] or _score > _highest['score']:
			_highest['score'] = _score
			_highest['item'] = ITEMS[item]
	
	if not _highest['item']:
		return True
	
	_empty_hand = lfe.get_open_hands(life)
	
	if not _empty_hand:
		print 'No open hands, managing....'
		for item_uid in lfe.get_held_items(life):
			_container = lfe.can_put_item_in_storage(life, item_uid)
			
			lfe.add_action(life, {'action': 'storeitem',
				'item': item_uid,
			     'container': _container},
				200,
				delay=lfe.get_item_access_time(life, item_uid))
		return False
	
	if life['pos'] == _highest['item']['pos']:
		lfe.clear_actions(life)
		
		for action in lfe.find_action(life, matches=[{'action': 'pickupholditem'}]):
			#print 'I was picking up something else...',_highest['item']['name']
			return False
		
		lfe.add_action(life,{'action': 'pickupholditem',
			'item': _highest['item']['uid'],
			'hand': random.choice(_empty_hand)},
			200,
			delay=lfe.get_item_access_time(life, _highest['item']))
		lfe.lock_item(life, _highest['item']['uid'])
	else:
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move','to': _highest['item']['pos'][:2]},200)
	
	return False

def find_target(life, target, distance=5, follow=False, call=True):
	print 'tar get', target, life['state']
	_target = brain.knows_alife_by_id(life, target)
	_dist = numbers.distance(life['pos'], _target['last_seen_at'])
	
	_can_see = sight.can_see_target(life, target)
	if _can_see and _dist<=distance:
		if not follow:
			return True
		
		lfe.stop(life)
	
	if _target['escaped'] == 1:
		search_for_target(life, target)
		return False
	
	if not _can_see and sight.can_see_position(life, _target['last_seen_at']) and _dist<distance:
		if call:
			if not _target['escaped']:
				memory.create_question(life, target, 'GET_LOCATION')
				
			speech.communicate(life, 'call', matches=[{'id': target}])
		
		_target['escaped'] = 1
		
		return False
	
	if not lfe.path_dest(life) == tuple(_target['last_seen_at'][:2]):
		lfe.clear_actions(life)
		lfe.add_action(life,
			          {'action': 'move','to': _target['last_seen_at'][:2]},
			          200)
	
	return False

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
