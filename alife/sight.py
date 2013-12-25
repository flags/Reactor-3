from globals import *
from fast_scan_surroundings import scan_surroundings as fast_scan_surroundings

import life as lfe

import judgement
import weather
import chunks
import brain
import logic
import items
import maps
import fov

import render_fast_los
import render_los
import numbers
import logging
import time


#@profile
def setup_look(life):
	if not 'CAN_SEE' in life['life_flags']:
		return False
	
	if life['path'] or not brain.get_flag(life, 'visible_chunks'):
		scan_surroundings(life, judge=False, get_chunks=True, ignore_chunks=0)

def look(life):
	for target_id in life['know']:
		if life['know'][target_id]['last_seen_time']:
			life['know'][target_id]['last_seen_time'] += 1
	
	#if life['think_rate'] % 3 and not 'player' in life:
	#	return False
	
	if not 'CAN_SEE' in life['life_flags']:
		return False
	
	if life['path'] or not brain.get_flag(life, 'visible_chunks'):
		if SETTINGS['smp']:
			_visible_chunks = post_scan_surroundings(life)
		else:
			_visible_chunks = scan_surroundings(life, judge=False, get_chunks=True, ignore_chunks=0)
			
		_chunks = [maps.get_chunk(c) for c in _visible_chunks]
		brain.flag(life, 'visible_chunks', value=_visible_chunks)
	elif 'player' in life:
		_visible_chunks = brain.get_flag(life, 'visible_chunks')
		_chunks = [maps.get_chunk(c) for c in _visible_chunks]
	else:
		#This is for optimizing. Be careful if you mess with this...
		_nearby_alife = []
		for alife in LIFE.values():
			if alife['id'] == life['id']:
				continue
			
			if numbers.distance(life['pos'], alife['pos'])<=get_vision(life) and can_see_position(life, alife['pos']):
				_nearby_alife.append(alife['pos'][:])
		
		_nearby_alife.sort()
		
		_last_nearby_alife = brain.get_flag(life, '_nearby_alife')
		
		if not _last_nearby_alife == _nearby_alife:
			brain.flag(life, '_nearby_alife', value=_nearby_alife)
		else:
			return False
		
		_chunks = [maps.get_chunk(c) for c in brain.get_flag(life, 'visible_chunks')]
	
	life['seen'] = []
	life['seen_items'] = []
	
	for item_uid in life['know_items']:
		life['know_items'][item_uid]['last_seen_time'] += 1
	
	for chunk in _chunks:
		judgement.judge_chunk_visually(life, '%s,%s' % (chunk['pos'][0], chunk['pos'][1]))
		judgement.judge_chunk_life(life, '%s,%s' % (chunk['pos'][0], chunk['pos'][1]))
		
		for ai in [LIFE[i] for i in chunk['life']]:
			if ai['id'] == life['id']:
				continue
			
			for target_id in life['know']:
				life['know'][target_id]['last_seen_time'] += 1
			
			if not is_in_fov(life, ai['pos']):
				continue
			
			life['seen'].append(ai['id'])
			
			if ai['id'] in life['know']:
				if life['think_rate'] == life['think_rate_max']:
					lfe.create_and_update_self_snapshot(LIFE[ai['id']])
					judgement.judge_life(life, ai['id'])
				
				if ai['dead']:
					if 'player' in life and not life['know'][ai['id']]['dead'] and life['know'][ai['id']]['last_seen_time']>10:
						logic.show_event('You discover the body of %s.' % ' '.join(ai['name']), life=ai)
					life['know'][ai['id']]['dead'] = True
				elif ai['asleep']:
					life['know'][ai['id']]['asleep'] = True
				
				life['know'][ai['id']]['last_seen_time'] = 0
				life['know'][ai['id']]['last_seen_at'] = ai['pos'][:]
				life['know'][ai['id']]['escaped'] = False
				life['know'][ai['id']]['state'] = ai['state']
				life['know'][ai['id']]['state_tier'] = ai['state_tier']
				
				if brain.alife_has_flag(life, ai['id'], 'search_map'):
					brain.unflag_alife(life, ai['id'], 'search_map')
				
				_chunk_id = lfe.get_current_chunk_id(ai)
				judgement.judge_chunk(life, _chunk_id, seen=True)
				
				continue
			
			brain.meet_alife(life, ai)
	
		for item in [ITEMS[i] for i in chunk['items'] if i in ITEMS]:
			if not is_in_fov(life, item['pos']):
				continue
			
			if not item['uid'] in life['know_items']:
				brain.remember_item(life, item)

			if items.is_item_owned(item['uid']):
				#TODO: This doesn't work because we are specifically checking chunks
				if item['owner'] and lfe.item_is_equipped(LIFE[item['owner']], item['uid']):
					life['know_items'][item['uid']]['last_seen_at'] = LIFE[item['owner']]['pos']
					life['know_items'][item['uid']]['last_owned_by'] = item['owner']
					life['know_items'][item['uid']]['last_seen_time'] = 0
				
				continue
			
			life['seen_items'].append(item['uid'])
			life['know_items'][item['uid']]['last_seen_at'] = item['pos'][:]
			life['know_items'][item['uid']]['last_seen_time'] = 0
			life['know_items'][item['uid']]['last_owned_by'] = None
			life['know_items'][item['uid']]['score'] = judgement.judge_item(life, item['uid'])
			life['know_items'][item['uid']]['lost'] = False

def get_vision(life):
	if not 'CAN_SEE' in life['life_flags']:
		return 0
	
	if 'player' in life:
		_fov_mod = 1
	else:
		_fov_mod = numbers.clip(1-(life['think_rate']/float(life['think_rate_max'])), 0.5, 1)
	
	_world_light = tcod.white-weather.get_lighting()
	_light_percentage = numbers.clip(((_world_light.r+_world_light.g+_world_light.b)*.30)/200.0, 0, 1)
	
	return int(round((life['vision_max']*_light_percentage)*_fov_mod))

#@profile
def _can_see_position(pos1, pos2, max_length=10, block_check=False, strict=False, distance=True):
	if block_check:
		_check = [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]
	else:
		_check = [(0, 0)]
	
	_ret_line = []
	for _pos in _check:
		_line = render_los.draw_line(pos1[0],
		                             pos1[1],
		                             pos2[0],
		                             pos2[1])
										 
		if not _line:
			_line = []
		
		if _pos == (0, 0):
			_ret_line = _line
		
		if len(_line) > max_length and distance:
			_ret_line = []
			continue
		
		for pos in _line:
			_chunk = chunks.get_chunk_from_cache(pos)
			
			for item_uid in _chunk['items'][:]:
				if not item_uid in ITEMS:
					_chunk['items'].remove(item_uid)
			
			for item in [ITEMS[uid] for uid in _chunk['items'] if items.is_blocking(uid)]:
				if tuple(item['pos'])[:2] == tuple(pos2)[:2]:
					continue
				
				if (pos[0], pos[1]) == tuple(item['pos'])[:2]:
					_ret_line = []
					if strict:
						return False
					
					continue
				
			if maps.is_solid((pos[0], pos[1], pos1[2]+1)):
				_ret_line = []
				if strict:
					return False
				
				continue
	
	return _ret_line

def is_in_fov(life, pos, view_size=MAP_WINDOW_SIZE):
	_min_los_x = ((life['fov'].shape[0]/2)-view_size[0]/2)
	_max_los_x = life['fov'].shape[0]
	_min_los_y = ((life['fov'].shape[1]/2)-view_size[1]/2)
	_max_los_y = life['fov'].shape[1]
	
	_x = pos[0]-(life['pos'][0]-life['fov'].shape[0])-life['fov'].shape[0]/2
	_y = pos[1]-(life['pos'][1]-life['fov'].shape[1])-life['fov'].shape[0]/2
	
	if _x<_min_los_x or _x>=_max_los_x or _y<_min_los_y or _y>=_max_los_y:
		return False
	
	return life['fov'][_x, _y] == 1

def can_see_position(life, pos, distance=True, block_check=False, strict=False, get_path=False):
	"""Returns `true` if the life can see a certain position."""
	if tuple(life['pos'][:2]) == tuple(pos[:2]):
		return [pos]
	
	if get_path:
		return _can_see_position(life['pos'], pos, max_length=get_vision(life), block_check=block_check, strict=strict, distance=distance)

	if is_in_fov(life, pos):
		return True
	
	return False

def can_see_target(life, target_id):
	if not target_id in LIFE:
		return False
		
	_knows = LIFE[target_id]
	_dist = numbers.distance(life['pos'], _knows['pos'])
	
	if _dist >= get_vision(life):
		return False
	
	_can_see = can_see_position(life, _knows['pos'])
	if not _can_see:
		return False
	
	return _can_see

def view_blocked_by_life(life, position, allow=[]):
	allow.append(life['id'])
	
	_avoid_positions = [tuple(LIFE[i]['pos'][:2]) for i in [l for l in LIFE if not l in allow]]
	_can_see = can_see_position(life, position, block_check=True, get_path=True)
	
	if not _can_see:
		return True
	
	for pos in _can_see:
		if pos in _avoid_positions:
			return True
	
	return False

def get_visiblity_of_position(life, pos):
	_distance = numbers.distance(life['pos'], pos)
	
	return 1-numbers.clip((_distance/float(get_vision(life))), 0, 1)

def generate_los(life, target, at, source_map, score_callback, invert=False, ignore_starting=False):
	_stime = time.time()
	_cover = {'pos': None,'score': 9000}
	
	_x = numbers.clip(at[0]-(SETTINGS['los']/2),0,MAP_SIZE[0]-(SETTINGS['los']/2))
	_y = numbers.clip(at[1]-(SETTINGS['los']/2),0,MAP_SIZE[1]-(SETTINGS['los']/2))
	_top_left = (_x,_y,at[2])
	
	target_los = render_fast_los.render_fast_los(at,
		SETTINGS['los'],
		source_map)
	
	for pos in render_los.draw_circle(life['pos'][0],life['pos'][1],30):
		x = pos[0]-_top_left[0]
		y = pos[1]-_top_left[1]
		
		if pos[0]<0 or pos[1]<0 or pos[0]>=MAP_SIZE[0] or pos[1]>=MAP_SIZE[0]:
			continue
		
		if x<0 or y<0 or x>=target_los.shape[1] or y>=target_los.shape[0]:
			continue
		
		if life['pos'][0]-_top_left[0]>=target_los.shape[1] or life['pos'][1]-_top_left[1]>=target_los.shape[0]:
			continue
		
		if target_los[life['pos'][1]-_top_left[1],life['pos'][0]-_top_left[0]]==invert and not ignore_starting:
			_cover['pos'] = life['pos'][:]
			return False
		
		if source_map[pos[0]][pos[1]][at[2]+1] or source_map[pos[0]][pos[1]][at[2]+2]:
			continue
		
		if target_los[y,x] == invert:
			#TODO: Additional scores, like distance from target
			_score = score_callback(life, target, pos)
			
			if _score<_cover['score']:
				_cover['score'] = _score
				_cover['pos'] = list(pos)
	
	#print time.time()-_stime
	if not _cover['pos']:
		print 'Nowhere to hide', target['life']['name'], _top_left
				
		return False
	
	return _cover

def _generate_los(life,target,at,source_map,score_callback,invert=False,ignore_starting=False):
	#Step 1: Locate cover
	_cover = {'pos': None,'score': 9000}
	
	#TODO: Unchecked Cython flag
	_x = numbers.clip(at[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0])
	_y = numbers.clip(at[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1])
	_top_left = (_x,_y,at[2])
	target_los = render_los.render_los(source_map,at,top_left=_top_left,no_edge=False)
	
	for pos in render_los.draw_circle(life['pos'][0],life['pos'][1],30):
		x = pos[0]-_top_left[0]
		y = pos[1]-_top_left[1]
		
		if pos[0]<0 or pos[1]<0 or pos[0]>=MAP_SIZE[0] or pos[1]>=MAP_SIZE[0]:
			continue
		
		if x<0 or y<0 or x>=target_los.shape[1] or y>=target_los.shape[0]:
			continue
		
		if life['pos'][0]-_top_left[0]>=target_los.shape[0] or life['pos'][1]-_top_left[1]>=target_los.shape[1]:
			continue
		
		if target_los[life['pos'][1]-_top_left[1],life['pos'][0]-_top_left[0]]==invert and not ignore_starting:
			_cover['pos'] = life['pos'][:]
			return False
		
		if source_map[pos[0]][pos[1]][at[2]+1] or source_map[pos[0]][pos[1]][at[2]+2]:
			continue
		
		if target_los[y,x] == invert:
			#TODO: Additional scores, like distance from target
			_score = score_callback(life,target['life'],pos)
			
			if _score<_cover['score']:
				_cover['score'] = _score
				_cover['pos'] = list(pos)
	
	if not _cover['pos']:
		print 'Nowhere to hide'		
		return False
	
	return _cover

def find_visible_items(life):
	return [item for item in life['know_items'].values() if not item['last_seen_time'] and not 'parent_id' in item['item']]

def find_known_items(life, matches={}, only_visible=True):
	_match = []
	
	_could_meet_with = []
	for need in brain.retrieve_from_memory(life, 'needs_to_meet'):
		_could_meet_with.extend(need['could_meet_with'])
	
	for item_uid in brain.get_matching_remembered_items(life, matches, no_owner=True, only_visible=only_visible):
		#TODO: Offload?
		_item = ITEMS[item_uid]
		
		_match.append(item_uid)
	
	return _match

def _scan_surroundings(center_chunk_key, chunk_size, vision, ignore_chunks=[], chunk_map=WORLD_INFO['chunk_map']):
	_center_chunk_pos = maps.get_chunk(center_chunk_key)['pos']
	#_center_chunk_pos[0] = ((_center_chunk_pos[0]/chunk_size)*chunk_size)+(chunk_size/2)
	#_center_chunk_pos[1] = ((_center_chunk_pos[1]/chunk_size)*chunk_size)+(chunk_size/2)
	_chunks = set()
	_chunk_map = set(chunk_map.keys())
	
	for _x_mod, _y_mod in render_los.draw_circle(0, 0, ((vision*2)/chunk_size)):
		x_mod = _center_chunk_pos[0]+(_x_mod*chunk_size) #(_x_mod/chunk_size)*chunk_size
		y_mod = _center_chunk_pos[1]+(_y_mod*chunk_size)
		#print x_mod, y_mod, _center_chunk_pos
		
		_chunk_key = '%s,%s' % (x_mod, y_mod)
		
		if _chunk_key in _chunks:
			continue
		
		if not ignore_chunks==0 and _chunk_key in ignore_chunks:
			continue
		elif isinstance(ignore_chunks, list):
			ignore_chunks.append(_chunk_key)
		
		if chunk_map and not _chunk_key in chunk_map:
			continue
		
		_chunks.add(_chunk_key)
	
	return list(_chunks)

def scan_surroundings(life, initial=False, _chunks=[], ignore_chunks=[], judge=True, get_chunks=False, visible_check=True):
	if _chunks:
		_chunk_keys = set(_chunks)
	else:
		_chunk_keys = set()
		
		if SETTINGS['smp']:
			fov.fov(life['pos'], get_vision(life), get_chunks=True, life_id=life['id'])
		else:
			life['fov'] = fov.fov(life['pos'], get_vision(life), callback=lambda pos: _chunk_keys.add(chunks.get_chunk_key_at(pos)))
	
	return list(_chunk_keys)

def post_scan_surroundings(life):
	_chunk_keys = set()
	_los = False
	_fov_job = FOV_JOBS[life['id']]
	_map, _keys = _fov_job()
	
	if _los:
		life['fov'] += _map
	else:
		life['fov'] = _map
		_los = True
	
	_chunk_keys.update(_keys)
	
	return list(_chunk_keys)