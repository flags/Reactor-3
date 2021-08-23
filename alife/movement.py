from globals import SELECTED_TILES, WORLD_INFO, SETTINGS, MAP_SIZE, ITEMS, LIFE

import life as lfe

from . import references
import weapons
import bad_numbers
from . import combat
from . import speech
from . import chunks
from . import memory
import logic
import alife
import zones
from . import sight
from . import brain
import maps
from . import jobs
import fov

import random

def position_to_attack(life, target, engage_distance):
	if lfe.find_action(life, [{'action': 'dijkstra_move', 'reason': 'positioning for attack'}]):
		if not lfe.ticker(life, 'attack_position', 4):
			return False
	
	_target_positions, _zones = combat.get_target_positions_and_zones(life, [target])
	_can_see = alife.sight.can_see_position(life, _target_positions[0], get_path=True)
	_distance = bad_numbers.distance(life['pos'], _target_positions[0])
	
	if _can_see and len(_can_see)<engage_distance*.85:
		if life['path']:
			lfe.stop(life)
	elif _distance<engage_distance*.9:
		_avoid_positions = set()
		_target_area = set()
			
		for life_id in alife.judgement.get_trusted(life, visible=False, only_recent=True):
			fov.fov(LIFE[life_id]['pos'], int(round(sight.get_vision(life)*.25)), callback=lambda pos: _avoid_positions.add(pos))
			
		fov.fov(_target_positions[0], int(round(sight.get_vision(life)*.15)), callback=lambda pos: _target_area.add(pos))
		
		_min_view_distance = int(round(sight.get_vision(life)*.25))
		_max_view_distance = int(round(sight.get_vision(life)*.5))
		_attack_positions = set(zones.dijkstra_map(life['pos'],
		                   _target_positions,
		                   _zones,
		                   rolldown=True,
		                   return_score_in_range=[_min_view_distance, _max_view_distance]))
		
		_attack_positions = _attack_positions - _target_area
		
		if not _attack_positions:
			return False
		
		if not lfe.find_action(life, [{'action': 'dijkstra_move', 'orig_goals': list(_attack_positions), 'avoid_positions': list(_avoid_positions)}]):
			lfe.stop(life)
			
			lfe.add_action(life, {'action': 'dijkstra_move',
		                          'rolldown': True,
		                          'goals': [list(p) for p in random.sample(_attack_positions, len(_attack_positions)//2)],
		                          'orig_goals': list(_attack_positions),
		                          'avoid_positions': list(_avoid_positions),
		                          'reason': 'positioning for attack'},
		                   999)
			
			return False
	else:
		_can_see_positions = set()
		_target_area = set()
		_avoid_positions = set()
		
		fov.fov(life['pos'], int(round(sight.get_vision(life)*.75)), callback=lambda pos: _can_see_positions.add(pos))
		fov.fov(_target_positions[0], int(round(sight.get_vision(life)*.75)), callback=lambda pos: _target_area.add(pos))
		
		for life_id in alife.judgement.get_trusted(life, visible=False, only_recent=True):
			_path_dest = lfe.path_dest(LIFE[life_id])
			
			if not _path_dest:
				continue
			
			if len(_path_dest)==2:
				_path_dest = list(_path_dest[:])
				_path_dest.append(LIFE[life_id]['pos'][2])
			
			fov.fov(_path_dest, 5, callback=lambda pos: _avoid_positions.add(pos))
		
		_avoid_positions = list(_avoid_positions)
		_sneak_positions = _can_see_positions - _target_area
		_move_positions = zones.dijkstra_map(LIFE[target]['pos'],
		                                     list(_sneak_positions),
		                                     _zones,
		                                     rolldown=True)
		
		if not _move_positions:
			travel_to_position(life, list(_target_positions[0]))
			return False
		
		if not lfe.find_action(life, [{'action': 'dijkstra_move', 'orig_goals': _move_positions, 'avoid_positions': _avoid_positions}]):
			lfe.stop(life)
			
			lfe.add_action(life, {'action': 'dijkstra_move',
		                          'rolldown': True,
		                          'goals': [list(p) for p in _move_positions],
		                          'orig_goals': _move_positions,
			                      'avoid_positions': _avoid_positions,
		                          'reason': 'positioning for attack'},
		                   999)
			
			return False
	
	return True

def travel_to_position(life, pos, stop_on_sight=False, force=False):
	if not bad_numbers.distance(life['pos'], pos):
		return True
	
	if stop_on_sight and sight.can_see_position(life, pos, get_path=True, ignore_z=True):
		lfe.stop(life)
		
		return True
	
	_dest = lfe.path_dest(life)
	if not force and _dest and tuple(_dest[:2]) == tuple(pos[:2]):
		return False
	
	lfe.walk_to(life, pos[:3])
	
	return False

def travel_to_chunk(life, chunk_key):
	_chunk_pos = maps.get_chunk(chunk_key)['pos']
	
	return travel_to_position(life, [_chunk_pos[0]+WORLD_INFO['chunk_size']//2, _chunk_pos[1]+WORLD_INFO['chunk_size']//2, 2])

def guard_chunk(life, chunk_key):
	if 'guard_time' in life['state_flags'] and life['state_flags']['guard_time']:
		life['state_flags']['guard_time'] -= 1
		
		return False
	
	life['state_flags']['guard_time'] = random.randint(45, 60)
	
	travel_to_chunk(life, chunk_key)
	
	return False

def set_focus_point(life, chunk_key):
	lfe.delete_memory(life, matches={'text': 'focus_on_chunk'})
	
	lfe.memory(life, 'focus_on_chunk', chunk_key=chunk_key)
	
	if 'player' in life:
		_center_chunk_pos = maps.get_chunk(chunk_key)['pos']
		_center_chunk_pos.append(2)
		
		logic.show_event('<Movement Order>', pos=_center_chunk_pos)

def pick_up_item(life, item_uid):
	_not_moved = travel_to_position(life, ITEMS[item_uid]['pos'])
	
	if _not_moved:
		lfe.add_action(life,{'action': 'pickupitem_npc',
		                     'item': item_uid},
		                     200,
		                     delay=lfe.get_item_access_time(life, item_uid))

def search_for_target(life, target_id):
	#TODO: Variable size instead of hardcoded
	_know = brain.knows_alife_by_id(life, target_id)
	_size = 30
	_timer = brain.get_flag(life, 'search_time')
	_chunk_path = alife.brain.get_flag(life, 'chunk_path')
	
	if _chunk_path:
		travel_to_position(life, _chunk_path['end'], force=True)
		
		return False
	
	if _timer>0:
		brain.flag(life, 'search_time', _timer-1)
		
		return False
	
	if brain.alife_has_flag(life, target_id, 'search_map'):
		_search_map = brain.get_alife_flag(life, target_id, 'search_map')
	else:
		_search_map = maps.create_search_map(life, _know['last_seen_at'], _size)
		brain.flag_alife(life, target_id, 'search_map', value=_search_map)
		
		lfe.walk_to(life, _know['last_seen_at'])
		brain.flag(life, 'search_time', 12)
		
		return False
	
	_lowest = {'score': -1, 'pos': None}
	_x_top_left = bad_numbers.clip(_know['last_seen_at'][0]-(_size//2), 0, MAP_SIZE[0])
	_y_top_left = bad_numbers.clip(_know['last_seen_at'][1]-(_size//2), 0, MAP_SIZE[1])
	
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
			
			if sight.can_see_position(life, (_x, _y, _know['last_seen_at'][2]), get_path=True) or not lfe.can_walk_to(life, (_x, _y, _know['last_seen_at'][2])):
				_search_map[y, x] = 0
			
			if _search_map[y, x]>0 and (not _lowest['pos'] or _search_map[y, x] < _lowest['score']):
				_lowest['score'] = _search_map[y, x]
				_lowest['pos'] = (_x, _y, x, y)

	if _lowest['pos']:
		x, y, _x, _y = _lowest['pos']
		
		if travel_to_position(life, (x, y, _know['last_seen_at'][2]), stop_on_sight=False):
			_search_map[_y, _x] = 0
		
		brain.flag(life, 'search_time', bad_numbers.clip(bad_numbers.distance(life['pos'], (x, y))*.75, 5, 16))
	else:
		_know['escaped'] = 2

def escape(life, targets):
	_avoid_positions = []
	_zones = [zones.get_zone_at_coords(life['pos'])]
	
	if lfe.find_action(life, [{'action': 'dijkstra_move', 'reason': 'escape'}]):
		if lfe.ticker(life, 'escape_refresh', 4):
			lfe.stop(life)
		else:
			return False
	
	for target_id in targets:
		_target = brain.knows_alife_by_id(life, target_id)
		_zone = zones.get_zone_at_coords(_target['last_seen_at'])
		
		if not _zone in _zones:
			_zones.append(_zone)
		
		_avoid_positions.append(_target['last_seen_at'])
	
	lfe.add_action(life, {'action': 'dijkstra_move',
	                      'rolldown': False,
	                      'zones': _zones,
	                      'goals': _avoid_positions,
	                      'reason': 'escape'},
	               100)

def hide(life, targets):
	_target_positions = []
	_avoid_positions = []
	_zones = [zones.get_zone_at_coords(life['pos'])]

	if lfe.find_action(life, [{'action': 'dijkstra_move', 'reason': 'escaping'}]):
		if not lfe.ticker(life, 'escaping', 6):
			return False

	#What can the targets see?
	for target_id in targets:
		_target = brain.knows_alife_by_id(life, target_id)
		_zone = zones.get_zone_at_coords(_target['last_seen_at'])

		if not _zone in _zones:
			_zones.append(_zone)

		fov.fov(_target['last_seen_at'], sight.get_vision(_target['life']), callback=lambda pos: _avoid_positions.append(pos))

	#What can we see?
	_can_see_positions = []
	fov.fov(life['pos'], sight.get_vision(life), callback=lambda pos: _can_see_positions.append(pos))

	#If there are no visible targets, we could be running away from a position we were attacked from
	_cover_exposed_at = brain.get_flag(life, 'cover_exposed_at')

	if _cover_exposed_at:
		_avoid_exposed_cover_positions = set()

		for pos in _cover_exposed_at[:]:
			if tuple(pos[:2]) in _can_see_positions:
				_cover_exposed_at.remove(pos)

				continue

			fov.fov(pos, int(round(sight.get_vision(life)*.25)), callback=lambda pos: _avoid_exposed_cover_positions.add(pos))

		for pos in _avoid_exposed_cover_positions:
			if not pos in _avoid_positions:
				_avoid_positions.append(pos)
	else:
		print('Something went wrong')

		return False

	#Overlay the two, finding positions we can see but the target can't
	for pos in _can_see_positions[:]:
		if pos in _avoid_positions:
			_can_see_positions.remove(pos)
			continue

		#Get rid of positions that are too close
		for target_id in targets:
			_target = brain.knows_alife_by_id(life, target_id)

			if bad_numbers.distance(_target['last_seen_at'], pos)<4:
				_can_see_positions.remove(pos)
				break

	#Now scan for cover to prevent hiding in the open
	for pos in _can_see_positions[:]:
		if chunks.get_chunk(chunks.get_chunk_key_at(pos))['max_z'] == 2:
			_can_see_positions.remove(pos)

	if not _can_see_positions:
		if life['pos'] in _cover_exposed_at:
			_cover_exposed_at.remove(life['pos'])

		return False

	if lfe.find_action(life, [{'action': 'dijkstra_move', 'goals': _can_see_positions[:]}]):
		return True

	lfe.stop(life)
	lfe.add_action(life, {'action': 'dijkstra_move',
	                      'rolldown': True,
	                      'zones': _zones,
	                      'goals': _can_see_positions[:],
	                      'reason': 'escaping'},
	               200)

	#print life['name'], 'here', tuple(life['pos'][:2]) in _can_see_positions

def collect_nearby_wanted_items(life, only_visible=True, matches={'type': 'gun'}):
	_highest = {'item': None,'score': -100000}
	_nearby = sight.find_known_items(life, matches=matches, only_visible=only_visible)
	
	for item in _nearby:
		_item = brain.get_remembered_item(life, item)
		_score = _item['score']
		_score -= bad_numbers.distance(life['pos'], ITEMS[item]['pos'])
		
		if not _highest['item'] or _score > _highest['score']:
			_highest['score'] = _score
			_highest['item'] = ITEMS[item]
	
	if not _highest['item']:
		return True
	
	_empty_hand = lfe.get_open_hands(life)
	
	if not _empty_hand:
		print('No open hands, managing....')
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
			delay=lfe.get_item_access_time(life, _highest['item']['uid']))
		lfe.lock_item(life, _highest['item']['uid'])
	else:
		lfe.walk_to(life, _highest['item']['pos'])
	
	return False

def find_target(life, target, distance=5, follow=False, call=True):
	_target = brain.knows_alife_by_id(life, target)
	_dist = bad_numbers.distance(life['pos'], _target['last_seen_at'])
	
	_can_see = sight.can_see_target(life, target)
	if _can_see and _dist<=distance:
		if follow:
			return True
		
		lfe.stop(life)
		
		return True
	
	if _target['escaped'] == 1:
		search_for_target(life, target)
		return False
	
	if not _can_see and sight.can_see_position(life, _target['last_seen_at']) and _dist<distance:
		if call:
			if not _target['escaped']:
				memory.create_question(life, target, 'GET_LOCATION')
				
			speech.communicate(life, 'call', matches=[target])
		
		_target['escaped'] = 1
		
		return False
	
	if not lfe.path_dest(life) == tuple(_target['last_seen_at'][:2]):
		lfe.walk_to(life, _target['last_seen_at'])
	
	return False

def follow_alife(life):
	if _find_alife(life, jobs.get_job_detail(life['job'], 'target'), distance=7):
		lfe.stop(life)
		return True
	
	return False

def _find_alife_and_say(life, target_id, say):
	_target = brain.knows_alife_by_id(life, target_id)
	
	if _find_alife(life, _target['life']['id']):
		speech.communicate(life, _say['gist'], matches=[_target['life']['id']], **say)
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
