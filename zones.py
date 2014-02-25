from globals import *

import libtcodpy as tcod
import graphics as gfx

import fast_dijkstra
import numbers
import alife
import maps
import smp

import logging
import numpy
import copy
import time

def cache_zones():
	for z in range(0, MAP_SIZE[2]):
		ZONE_CACHE[z] = [s for s in WORLD_INFO['slices'].values() if s['z'] == z]

def create_map_array(val=0, size=MAP_SIZE):
	_map = numpy.zeros((size[0], size[1]))
	_map+=val
	
	return _map

#@profile
def get_unzoned(slice_map, positions, z, map_size=MAP_SIZE):
	for x,y in positions:
		if not slice_map[x][y]:
			return x,y

	return None

#@profile
def process_slice(z, world_info=None, start_id=0, map_size=MAP_SIZE):
	print 'Processing:', z
	_runs = 0
	_slice = create_map_array(size=map_size)
	_ground = []
	_unzoned = {}
	
	for y in range(map_size[1]):
		for x in range(map_size[0]):
			if not WORLD_INFO['map'][x][y][z]:# or not maps.is_solid((x, y, z)):
				continue
		
			if maps.is_solid((x, y, z)) and z>0 and z<=map_size[2]:
				if maps.is_solid((x, y, z+1)) and maps.is_solid((x, y, z-1)):
					continue
			
			_unzoned[(x, y)] = None
	
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
		_start_pos = get_unzoned(_slice, _unzoned, z, map_size=map_size)
		
		if _start_pos:
			print '\tNew zone:', _z_id
		else:
			print '\tRuns for zone id %s: %s' % (_z_id, _runs)
			break
		
		_slice[_start_pos[0]][_start_pos[1]] = _z_id
		_ground = [_start_pos]
		del _unzoned[_start_pos]
		_top_left = [map_size[0], map_size[1]]
		_bot_right = [0, 0]
		_to_check = [_start_pos]
		
		if _start_pos[0] < _top_left[0]:
			_top_left[0] = _start_pos[0]
		if _start_pos[1] < _top_left[1]:
			_top_left[1] = _start_pos[1]
			
		if _start_pos[0] > _bot_right[0]:
			_bot_right[0] = _start_pos[0]
		if _start_pos[1] > _bot_right[1]:
			_bot_right[1] = _start_pos[1]
		
		while _to_check:
			_per_run = time.time()
			_runs += 1
			
			x,y = _to_check.pop(0)
			
			_skip_ramp_check = False
			if z == 2:
				if WORLD_INFO['chunk_map'][alife.chunks.get_chunk_key_at((x, y))]['max_z'] == z:
					_skip_ramp_check = True
			
			if not _slice[x][y] == _z_id:
				continue
			
			for x_mod,y_mod in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
				_x = x+x_mod
				_y = y+y_mod
				
				if _x<0 or _x>=map_size[0] or _y<0 or _y>=map_size[1]:
					continue
				
				#if maps.is_solid((_x, _y, z+1)) and maps.is_solid((_x, _y, z-1)):
				#	print 'both solid!!!!!!!!!!!'
				#	continue
				
				if (_x, _y) in _unzoned and not (_slice[_x][_y]):
					_slice[_x][_y] = _z_id
					_ground.append((_x, _y))
					del _unzoned[(_x, _y)]
					
					if _x < _top_left[0]:
						_top_left[0] = _x
					if _y < _top_left[1]:
						_top_left[1] = _y
						
					if _x > _bot_right[0]:
						_bot_right[0] = _x
					if _y > _bot_right[1]:
						_bot_right[1] = _y
					
					#if not (_x, _y) in _to_check:
					_to_check.append((_x, _y))
					#else:
					#	print 'dupe'
				
				if _skip_ramp_check:
					continue
				
				if (_x, _y, z+1) in _ramps or (_x, _y, z-1) in _ramps:
					continue
				
				#Above, Below
				if z < map_size[2]-1 and maps.get_tile((_x, _y, z+1)) and maps.is_solid((_x, _y, z+1)):
					if z < map_size[2]-2 and maps.get_tile((_x, _y, z+2)) and maps.is_solid((_x, _y, z+2)):
						pass
					else:
						if (_x, _y, z+1) in _ramps:
							continue
						
						_ramps.add((_x, _y, z+1))
						continue
				
				elif z and (not maps.get_tile((_x, _y, z)) or not maps.is_solid((_x, _y, z))) and maps.is_solid((_x, _y, z-1)):
					if (_x, _y, z-1) in _ramps:
						print 'panic'
						continue
					
					_ramps.add((_x, _y, z-1))
		
		for pos in _ground:
			WORLD_INFO['map'][pos[0]][pos[1]][z]['z_id'] = _z_id
		
		print '\t\tRun %s: %s seconds, %s ramps' % (_runs, time.time()-_per_run, len(_ramps))
		
		if world_info:
			return {'z': z, 'id': _z_id, 'ramps': list(_ramps), 'neighbors': {}}
		else:
			WORLD_INFO['slices'][_z_id] = {'z': z, 'top_left': _top_left, 'bot_right': _bot_right, 'id': _z_id, 'ramps': list(_ramps), 'neighbors': {}}

def get_zone_at_coords(pos):
	_map_pos = WORLD_INFO['map'][pos[0]][pos[1]][pos[2]]
	
	if not _map_pos or not 'z_id' in _map_pos:
		return None
	
	return _map_pos['z_id']

def get_slice(zone_id):
	zone_id = str(zone_id)
	return WORLD_INFO['slices'][zone_id]

def get_slices_at_z(z):
	return ZONE_CACHE[z]
	#return [s for s in WORLD_INFO['slices'].values() if s['z'] == z]

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
	#WORLD_INFO['slice_map'] = maps.create_map()
	WORLD_INFO['zoneid'] = 1
	
	if SETTINGS['running']:
		tcod.console_set_default_foreground(0, tcod.white)
		tcod.console_flush()
	
	_t = time.time()
	if SETTINGS['smp']:
		smp.create_zone_maps()
	else:
		for z in range(MAP_SIZE[2]):
			gfx.title('Zoning: %s\%s' % (z+1, MAP_SIZE[2]))
			process_slice(z)
	
		if SETTINGS['running']:
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
				if _matched_slice['id']>0:
					if not _matched_slice['id'] in WORLD_INFO['slices'][_slice]['neighbors']:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['id']] = [(x, y)]
					elif not (x, y) in WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['id']]:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['id']].append((x, y))
		
		del WORLD_INFO['slices'][_slice]['ramps']

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
