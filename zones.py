from globals import *

import libtcodpy as tcod
import graphics as gfx

import fast_dijkstra
import numbers
import maps
import smp

import logging
import copy
import time

def cache_zones():
	for z in range(0, MAP_SIZE[2]):
		ZONE_CACHE[z] = get_slices_at_z(z)

def create_map_array(val=0, size=MAP_SIZE):
	_map = []
	for x in range(size[0]):
		_y = []
		
		for y in range(size[1]):
			_y.append(val)
		
		_map.append(_y)
	
	return _map

def get_unzoned(slice_map, z, map_size=MAP_SIZE):
	for x in range(map_size[0]):
		for y in range(map_size[1]):
			if not WORLD_INFO['map'][x][y][z]:# or (z<MAP_SIZE[2]-1 and not MAP[x][y][z+1]):
				continue
			
			if slice_map[x][y]:
				continue
			
			if not slice_map[x][y]:
				return x,y
	
	return None

#@profile
def process_slice(z, world_info=None, start_id=0, map_size=MAP_SIZE):
	print 'Processing:', z
	_runs = 0
	_slice = create_map_array(size=map_size)
	
	if world_info:
		WORLD_INFO.update(world_info)
		
	for x in range(map_size[0]):
		for y in range(map_size[1]):
			if z < map_size[2]-1 and maps.is_solid((x, y, z+1)):
				if z < map_size[2]-2 and maps.is_solid((x, y, z+2)):
					_slice[x][y] = -2
				else:
					_slice[x][y] = -1
	
	while 1:
		if world_info:
			start_id += 1
			_z_id = start_id
		else:
			WORLD_INFO['zoneid'] += 1
			_z_id = WORLD_INFO['zoneid']
		
		_ramps = set()
		_start_pos = get_unzoned(_slice, z, map_size=map_size)
		
		if not _start_pos:
			print '\tRuns for zone id %s: %s' % (_z_id, _runs)
			break
		else:
			print '\tNew zone:', _z_id
		
		_slice[_start_pos[0]][_start_pos[1]] = _z_id
		
		_changed = True
		while _changed:
			_per_run = time.time()
			_runs += 1
			_changed = False
			
			for x in range(map_size[0]):
				for y in range(map_size[1]):
					if not _slice[x][y] == _z_id:
						continue
					
					for x_mod,y_mod in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
						_x = x+x_mod
						_y = y+y_mod
						
						if _x<0 or _x>=map_size[0] or _y<0 or _y>=map_size[1]:
							continue
						
						if maps.is_solid((_x, _y, z)) and not (_slice[_x][_y] == _z_id or _slice[_x][_y] in [-2, -1]):
							_slice[_x][_y] = _z_id
							_changed = True
						
						#Above, Below
						if z < map_size[2]-1 and maps.is_solid((_x, _y, z+1)):
							if z < map_size[2]-2 and maps.is_solid((_x, _y, z+2)):
								pass
							else:
								if (_x, _y, z+1) in _ramps:
									print 'panic (2)'
									continue
								
								_ramps.add((_x, _y, z+1))
								continue
						
						elif z and not maps.is_solid((_x, _y, z)) and maps.is_solid((_x, _y, z-1)):
							if (_x, _y, z-1) in _ramps:
								print 'panic'
								continue
							
							_ramps.add((_x, _y, z-1))
			
			print '\t\tRun %s: %s seconds, %s ramps' % (_runs, time.time()-_per_run, len(_ramps))
	
		#NOTE: If stuff starts breaking, remove the condition:
		
		if world_info:
			return {'z': z, 'id': _z_id, 'map': _slice, 'ramps': list(_ramps), 'neighbors': {}}
		else:
			WORLD_INFO['slices'][_z_id] = {'z': z, 'id': _z_id, 'map': copy.deepcopy(_slice), 'ramps': list(_ramps), 'neighbors': {}}

def get_zone_at_coords(pos):
	for _splice in ZONE_CACHE[pos[2]]:
		if _splice['map'][pos[0]][pos[1]]>0:
			return _splice['map'][pos[0]][pos[1]]
	
	return None

def get_slice(zone_id):
	zone_id = str(zone_id)
	return WORLD_INFO['slices'][zone_id]

def get_slices_at_z(z):
	return [s for s in WORLD_INFO['slices'].values() if s['z'] == z]

def can_path_to_zone(z1, z2):
	if z1 == z2:
		return [z1]
	
	z1 = str(z1)
	z2 = str(z2)
	
	_checked = []
	_to_check = [z1]
	
	while _to_check:
		_checking = _to_check.pop()
		_checked.append(_checking)
		
		if _checking:
			return []
		
		try:
			_to_check.extend([n for n in WORLD_INFO['slices'][_checking]['neighbors'] if _checking and not n in _checked])
		except:
			raise Exception('Failed.')
		
		if z2 in _to_check:
			_checked.append(z2)
			return _checked
	
	return []

def create_zone_map():
	WORLD_INFO['slices'] = {}
	WORLD_INFO['zoneid'] = 1
	tcod.console_set_default_foreground(0, tcod.white)
	tcod.console_flush()
	
	_t = time.time()
	if SETTINGS['smp']:
		smp.create_zone_maps()
	else:
		for z in range(MAP_SIZE[2]):
			gfx.title('Zoning: %s\%s' % (z+1, MAP_SIZE[2]))
			process_slice(z)
	
		tcod.console_print(0, 0, 0, '              ')
	print 'Zone gen took',time.time()-_t

def connect_ramps():
	_i = 1
	
	for _slice in WORLD_INFO['slices']:
		print 'Connecting:','Zone %s' % _slice, '@ z-level',WORLD_INFO['slices'][_slice]['z'], '(%s ramp(s))' % len(WORLD_INFO['slices'][_slice]['ramps'])
		gfx.title('Connecting: %s\%s' % (_i, len(WORLD_INFO['slices'].keys())))
		
		_i += 1
		
		for x,y,z in WORLD_INFO['slices'][_slice]['ramps']:
			for _matched_slice in get_slices_at_z(z):
				if _matched_slice['map'][x][y]>0:
					if not _matched_slice['map'][x][y] in WORLD_INFO['slices'][_slice]['neighbors']:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]] = [(x, y)]
					elif not (x, y) in WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]]:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]].append((x, y))

#@profile
def dijkstra_map(start_pos, goals, zones, max_chunk_distance=5, rolldown=True, avoid_chunks=[], avoid_positions=[], return_score=False, return_score_in_range=[]):
	if not goals:
		raise Exception('No goals set for dijkstra map.')
	
	if not zones:
		raise Exception('No zones set for dijkstra map.')
	
	_map = {'start_pos': start_pos,
	        'goals': goals,
	        'zones': zones,
	        'max_chunk_distance': max_chunk_distance,
	        'rolldown': rolldown,
	        'avoid_chunks': avoid_chunks,
	        'avoid_positions': avoid_positions,
	        'return_score': return_score,
	        'return_score_in_range': return_score_in_range}
	
	_map_string = ''
	for key in _map.keys():
		_map_string += '%s:%s' % (key, _map[key])
	
	if _map_string in DIJKSTRA_CACHE:
		return DIJKSTRA_CACHE[_map_string]['return']
	
	_map['return'] = fast_dijkstra.dijkstra_map(start_pos,
	                                  goals,
	                                  zones,
	                                  max_chunk_distance=max_chunk_distance,
	                                  rolldown=rolldown,
	                                  avoid_chunks=avoid_chunks,
	                                  avoid_positions=avoid_positions,
	                                  return_score=return_score,
	                                  return_score_in_range=return_score_in_range)
	
	DIJKSTRA_CACHE[_map_string] = _map
	
	return _map['return']

def slow_dijkstra_map(goals, zones, max_chunk_distance=5):
	_open_map = create_map_array(val=-3)
	_chunk_keys = {}
	_top_left = MAP_SIZE[:2]
	_bot_right = [0, 0]
	
	#0: Banned
	#1: Open
	
	for zone in [get_slice(z) for z in zones]:
		for y in range(0, MAP_SIZE[1]-1):
			for x in range(0, MAP_SIZE[0]-1):
				if _open_map[x][y]>-3:
					continue
				
				if not zone['map'][x][y] == zone['id'] or zone['map'][x][y] in [-2, -1]:
					continue
				
				_open_map[x][y] = 1
				
				_chunk_key = '%s,%s' % ((x/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'], (y/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'])
				_chunk = WORLD_INFO['chunk_map'][_chunk_key]
				
				_pass = False
				for goal in goals:
					_goal_chunk_key = '%s,%s' % ((goal[0]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'], (goal[1]/WORLD_INFO['chunk_size'])*WORLD_INFO['chunk_size'])
					_goal_chunk = WORLD_INFO['chunk_map'][_goal_chunk_key]
					
					if numbers.distance(_chunk['pos'], _goal_chunk['pos'])/WORLD_INFO['chunk_size']<=max_chunk_distance:
						_pass = True
						break
				
				if not _pass:
					continue
				
				#Return open map...
				if x<_top_left[0]:
					_top_left[0] = x
					
				if y<_top_left[1]:
					_top_left[1] = y
				
				if x>_bot_right[0]:
					_bot_right[0] = x
				
				if y>_bot_right[1]:
					_bot_right[1] = y
				
				_chunk_keys[_chunk_key] = zone['id']
	
	_map_info = {'open_map': _open_map,
	             'size': (_bot_right[0]-_top_left[0], _bot_right[1]-_top_left[1]),
	             'top_left': _top_left,
	             'bot_right': _bot_right}
	_map_info['map'] = create_map_array(size=_map_info['size'])
	
	for y in range(0, _map_info['size'][1]):
		for x in range(0, _map_info['size'][0]):
			_x = x+_map_info['top_left'][0]
			_y = y+_map_info['top_left'][1]
	
			if _map_info['open_map'][_x][_y]<=0:
				_map_info['map'][x][y] = -99999
				#_map_info['map'][x][y] = _map_info['open_map'][_x][
			else:
				_map_info['map'][x][y] = 99999
	
	for goal in goals:
		_x = goal[0]-_map_info['top_left'][0]
		_y = goal[1]-_map_info['top_left'][1]
		
		_map_info['map'][_x][_y] = 0
	
	_changed = True
	while _changed:
		_changed = False
		_old_map = copy.deepcopy(_map_info['map'])
		
		for y in range(0, _map_info['size'][1]):
			for x in range(0, _map_info['size'][0]):
				if _old_map[x][y]<=0:
					continue
				
				_lowest_score = _old_map[x][y]
				
				for pos in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
					_x = x+pos[0]
					_y = y+pos[1]
					
					if _x<0 or _x>=_map_info['size'][0] or _y<0 or _y>=_map_info['size'][1]:
						continue
					
					if _old_map[_x][_y]<0:
						continue
					
					_score = _old_map[_x][_y]
					
					if _score<_lowest_score:
						_lowest_score = _score
					
				if _old_map[x][y]-_lowest_score>=2:
					_map_info['map'][x][y] = _lowest_score+1
					_changed=True
	
	#for y in range(0, _map_info['size'][1]):
	#	for x in range(0, _map_info['size'][0]):
	#		if _map_info['map'][x][y]>0:
	#			print numbers.clip(_map_info['map'][x][y], 0, 9),
	#		else:
	#		#	#elif _map_info['map'][x][y] == -3:
	#			print '#',
	#			#else:
	#			#print _map_info['map'][x][y],#'#',
	#	
	#	print