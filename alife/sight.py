from globals import *

import life as lfe

import judgement
import chunks
import brain
import logic
import maps

import render_fast_los
import render_los
import numbers
import logging
import time

#@profile
def look(life):
	life['seen'] = []
	
	if not 'CAN_SEE' in life['life_flags']:
		return False
	
	_chunks = []
	if SETTINGS['smp']:
		_visible_chunks = [c for c in brain.get_flag(life, 'nearby_chunks') if c in WORLD_INFO['chunk_map']]
		_chunks = [maps.get_chunk(c) for c in scan_surroundings(life, _chunks=_visible_chunks, judge=False, ignore_chunks=0, get_chunks=True)]
		brain.flag(life, 'visible_chunks', value=_visible_chunks)
	else:
		_visible_chunks = scan_surroundings(life, judge=False, get_chunks=True, ignore_chunks=0, visible_check=False)
		#_visible_chunks = fast_scan_surroundings(life, judge=False, get_chunks=True, ignore_chunks=0)
		_chunks = [maps.get_chunk(c) for c in _visible_chunks]
		brain.flag(life, 'visible_chunks', value=_visible_chunks)
	
	if not _chunks:
		_chunks = [maps.get_chunk(c) for c in brain.get_flag(life, 'visible_chunks')]
	
	for ai in life['know'].values():
		ai['last_seen_time'] += 1
	
	for chunk in _chunks:
		for ai in [LIFE[i] for i in chunk['life']]:
			if ai['id'] == life['id']:
				continue
			
			if not can_see_target(life, ai['id']):
				continue
			
			if ai['id'] in life['know']:
				life['know'][ai['id']]['last_seen_time'] = 0
			
			life['seen'].append(ai['id'])
			
			if ai['id'] in life['know']:
				if life['think_rate'] == life['think_rate_max']:
					lfe.create_and_update_self_snapshot(LIFE[ai['id']])
					judgement.judge(life, ai['id'])
				
				life['know'][ai['id']]['last_seen_time'] = 0
				life['know'][ai['id']]['last_seen_at'] = ai['pos'][:]
				life['know'][ai['id']]['escaped'] = False
				
				if brain.alife_has_flag(life, ai['id'], 'search_map'):
					brain.unflag_alife(life, ai['id'], 'search_map')
				
				_chunk_id = lfe.get_current_chunk_id(ai)
				judgement.judge_chunk(life, _chunk_id)
				
				continue
			
			brain.meet_alife(life, ai)
	
		for item in [ITEMS[i] for i in chunk['items']]:
			if item.has_key('id') or item.has_key('parent'):
				continue
			
			_can_see = can_see_position(life, item['pos'])
			if _can_see:
				if not item['uid'] in life['know_items']:
					brain.remember_item(life, item)
				elif not life['know_items'][item['uid']]['last_seen_time']:
					continue
	
				life['know_items'][item['uid']]['last_seen_time'] = 0
				life['know_items'][item['uid']]['score'] = judgement.judge_item(life, item)
			elif item['uid'] in life['know_items']:
				life['know_items'][item['uid']]['last_seen_time'] += 1

def get_vision(life):
	if not 'CAN_SEE' in life['life_flags']:
		return 0
	
	#TODO: Fog? Smoke? Light?
	#if logic.is_night():
	#	if WORLD_INFO['real_time_of_day']>=WORLD_INFO['length_of_day']-1500:
	#		_time = WORLD_INFO['real_time_of_day']-(WORLD_INFO['length_of_day']-1500)
	#	else:
	#		_time = WORLD_INFO['real_time_of_day']
	#	
	#	return int(life['vision_max']*(_time/1500.0))
	
	return life['vision_max']

def _can_see_position(pos1, pos2):
	_line = render_los.draw_line(pos1[0],
		pos1[1],
		pos2[0],
		pos2[1])
		
	if not _line:
		_line = []
	
	for pos in _line:
		if WORLD_INFO['map'][pos[0]][pos[1]][pos1[2]+1]:
			return False
	
	return _line

def can_see_position(life, pos, distance=True, block_check=False):
	"""Returns `true` if the life can see a certain position."""
	if tuple(life['pos'][:2]) == tuple(pos[:2]):
		return [pos]
	
	if block_check:
		_check = [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)]
	else:
		_check = [(0, 0)]
	
	_ret_line = []
	for _pos in _check:
		_line = render_los.draw_line(life['pos'][0]+_pos[0],
			life['pos'][1]+_pos[1],
			pos[0],
			pos[1])
			
		if not _line:
			_line = []
		
		if _pos == (0, 0):
			_ret_line = _line
		
		if len(_line) >= get_vision(life) and distance:
			return False	
		
		for pos in _line:
			if WORLD_INFO['map'][pos[0]][pos[1]][life['pos'][2]+1]:
				return False
	
	return _ret_line

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
	_can_see = can_see_position(life, position, block_check=True)
	
	if not _can_see:
		return True
	
	for pos in _can_see:
		if pos in _avoid_positions:
			return True
	
	return False

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
	#Destktop
	#New: 0.0127160549164
	#Old: 0.0237522125244
	
	#Laptop:
	#New: 0.0139999389648
	#Old: 0.0350000858307
	
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

def handle_lost_los(life):
	#TODO: Take the original score and subtract/add stuff from there...
	_nearest_target = {'target': None,'score': 0}
	for entry in life['know']:
		_target = life['know'][entry]
		_score = judgement.judge(life,_target)
		
		if _target['escaped']:
			_score += (_target['last_seen_time']/2)
		
		if _score < _nearest_target['score']:
			_nearest_target['target'] = _target
			_nearest_target['score'] = _score
	
	return _nearest_target

def find_visible_items(life):
	return [item for item in life['know_items'].values() if not item['last_seen_time'] and not 'parent_id' in item['item']]

def find_known_items(life, matches={}, visible=True):
	_match = []
	
	for item in [life['know_items'][item] for item in life['know_items']]:
		if not item['item']['uid'] in ITEMS:
			continue
		
		if visible and not can_see_position(life, item['item']['pos']):
			continue
		
		if 'parent' in item['item'] or 'parent_id' in item['item']:
			continue
		
		if 'demand_drop' in item['flags']:
			continue
		
		if item['item']['lock']:
			continue
		
		_break = False
		for key in matches:
			if not item['item'].has_key(key) or not item['item'][key] == matches[key]:
				_break = True
				break
		
		if _break:
			continue
		
		_match.append(item)
	
	return _match

def _scan_surroundings(center_chunk_key, chunk_size, vision, ignore_chunks=[], chunk_map=WORLD_INFO['chunk_map']):
	_chunks = []
	
	for x_mod in range((-vision/chunk_size)+1, (vision/chunk_size)+1):
		for y_mod in range((-vision/chunk_size)+1, (vision/chunk_size)+1):
			_pos_mod = [x_mod*chunk_size, y_mod*chunk_size]
			_chunk_key = ','.join([str(int(val)+_pos_mod.pop()) for val in center_chunk_key.split(',')])
			
			if not ignore_chunks==0 and _chunk_key in ignore_chunks:
				continue
			elif isinstance(ignore_chunks, list):
				ignore_chunks.append(_chunk_key)
			
			if chunk_map and not _chunk_key in chunk_map:
				continue
			
			_chunks.append(_chunk_key)
	
	return _chunks

def scan_surroundings(life, initial=False, _chunks=[], ignore_chunks=[], judge=True, get_chunks=False, visible_check=True):
	_center_chunk_key = lfe.get_current_chunk_id(life)
	
	if get_chunks:
		_center_chunk = maps.get_chunk(_center_chunk_key)
	
	_visible_chunks = []
	
	if _chunks:
		_chunks = [c for c in _chunks if c in WORLD_INFO['chunk_map']]
	else:
		_chunks = _scan_surroundings(_center_chunk_key, WORLD_INFO['chunk_size'], get_vision(life)/2, ignore_chunks=ignore_chunks)
		_chunks = [c for c in _chunks if c in WORLD_INFO['chunk_map']]
	
	for chunk_key in _chunks:
		if visible_check and not chunks.can_see_chunk(life, chunk_key):
			continue
		
		if not chunk_key in WORLD_INFO['chunk_map']:
				continue
		
		if get_chunks:
			_current_chunk = maps.get_chunk(chunk_key)
			_visible_chunks.append(chunk_key)
			
			_current_chunk_pos = (_current_chunk['pos'][0]/WORLD_INFO['chunk_size'], _current_chunk['pos'][1]/WORLD_INFO['chunk_size'])
			_center_chunk_pos = (_center_chunk['pos'][0]/WORLD_INFO['chunk_size'], _center_chunk['pos'][1]/WORLD_INFO['chunk_size'])
			_direction = (_current_chunk_pos[0]-_center_chunk_pos[0], _current_chunk_pos[1]-_center_chunk_pos[1])
		
		if judge:
			if initial:
				judgement.judge_chunk(life, chunk_key, seen=True)
			else:
				judgement.judge_chunk(life, chunk_key)
	
	if get_chunks:
		return _visible_chunks

def fast_scan_surroundings(life, initial=False, _chunks=[], ignore_chunks=[], judge=True, get_chunks=False):
	_vision = get_vision(life)/2
	_center_chunk_key = lfe.get_current_chunk_id(life)
	_limit = _vision/WORLD_INFO['chunk_size']
	_outside_chunks = []
	_inside_chunks = []
	_visible_chunks = []
	
	for x_mod in range((-_vision/WORLD_INFO['chunk_size'])+1, (_vision/WORLD_INFO['chunk_size'])+1):
		for y_mod in range((-_vision/WORLD_INFO['chunk_size'])+1, (_vision/WORLD_INFO['chunk_size'])+1):
			_pos_mod = [x_mod*WORLD_INFO['chunk_size'], y_mod*WORLD_INFO['chunk_size']]
			_chunk_key = ','.join([str(int(val)+_pos_mod.pop()) for val in _center_chunk_key.split(',')])
			
			if not _chunk_key in WORLD_INFO['chunk_map']:
				continue
			
			if not ignore_chunks==0 and _chunk_key in ignore_chunks:
				continue
			elif isinstance(ignore_chunks, list):
				ignore_chunks.append(_chunk_key)
			
			#if chunk_map and not _chunk_key in chunk_map:
			#	continue
			
			if (x_mod == -_limit or x_mod == _limit) or (y_mod == -_limit or y_mod == _limit):
				_outside_chunks.append(_chunk_key)
			else:
				_inside_chunks.append(_chunk_key)
			
			#_chunks.append(_chunk_key)
	
	for chunk_key in _outside_chunks:
		_can_see = chunks.can_see_chunk(life, chunk_key)
		
		if not _can_see:
			continue
		
		for pos in _can_see:
			_pos_chunk_key = chunks.get_chunk_key_at(pos)
			
			if not _pos_chunk_key in _visible_chunks:
				_visible_chunks.append(_pos_chunk_key)
	
	return _visible_chunks
		