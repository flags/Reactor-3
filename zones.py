from globals import *

import time

def create_map_array():
	_map = []
	for x in range(MAP_SIZE[0]):
		_y = []
		
		for y in range(MAP_SIZE[1]):
			_y.append(0)
		
		_map.append(_y)
	
	return _map

def get_unzoned(slice_map, z):
	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			if not WORLD_INFO['map'][x][y][z]:# or (z<MAP_SIZE[2]-1 and not MAP[x][y][z+1]):
				continue
			
			if slice_map[x][y]:
				continue
			
			if not slice_map[x][y]:
				return x,y
	
	return None

def process_slice(z):
	print 'Processing:',z
	_runs = 0
	_slice = create_map_array()
	
	while 1:
		WORLD_INFO['zoneid'] += 1
		_z_id = WORLD_INFO['zoneid']
		_ramps = []
		_start_pos = get_unzoned(_slice, z)
		
		if not _start_pos:
			#draw_slice(_slice)
			#draw_map(MAP, z)
			print '\tRuns:',_runs,'Time:',
			break
		
		_slice[_start_pos[0]][_start_pos[1]] = _z_id
		
		_changed = True
		while _changed:
			_runs += 1
			_changed = False
			
			for x in range(MAP_SIZE[0]):
				for y in range(MAP_SIZE[1]):
					if not _slice[x][y] == _z_id:
						continue
					
					for x_mod,y_mod in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
						_x = x+x_mod
						_y = y+y_mod
						
						if _x<0 or _x>=MAP_SIZE[0] or _y<0 or _y>=MAP_SIZE[1]:
							continue
						
						if WORLD_INFO['map'][_x][_y][z] and not _slice[_x][_y] == _z_id:
							_slice[_x][_y] = _z_id
							_changed = True
						
						if z < MAP_SIZE[2]-1 and WORLD_INFO['map'][_x][_y][z+1]:
							_ramps.append((_x, _y, z+1))
						elif not WORLD_INFO['map'][_x][_y][z] and z and WORLD_INFO['map'][_x][_y][z-1]:
							_ramps.append((_x, _y, z-1))
	
		WORLD_INFO['slices'][_z_id] = {'z': z, 'map': _slice, 'ramps': _ramps, 'neighbors': {}}

def get_zone_at_coords(pos):
	for _splice in get_slices_at_z(pos[2]):
		if _splice['map'][pos[0]][pos[1]]:
			return _splice['map'][pos[0]][pos[1]]
	
	return None

def get_slices_at_z(z):
	return [s for s in WORLD_INFO['slices'].values() if s['z'] == z]

def can_path_to_zone(z1, z2, checked=[], path=[]):
	z1 = int(z1)
	z2 = int(z2)
	
	if z1 == z2:
		#TODO: BROKEN: SHOULD RETURN ZONE
		return True
	
	#if not path:
	#	path.append(z1)
	
	checked.append(z1)
	#print checked
	
	if z2 in WORLD_INFO['slices'][z1]['neighbors']:
		path.append(z2)
		#path.append(z1)
		return path
	
	_neighbors = [n for n in WORLD_INFO['slices'][z1]['neighbors'] if not n in checked]
	
	if not _neighbors:
		return False
	
	for _neighbor in _neighbors:
		_zone = can_path_to_zone(_neighbor, z2, checked=checked, path=path)
		if _zone:
			#path.extend(_zone)
			return path
		
	
	return False

def create_zone_map():
	for z in range(MAP_SIZE[2]):
		_stime = time.time()
		process_slice(z)
		print time.time()-_stime

def connect_ramps():
	for _slice in WORLD_INFO['slices']:
		print 'Connecting:','Zone %s' % _slice, '@ z-level',WORLD_INFO['slices'][_slice]['z']
		for x,y,z in WORLD_INFO['slices'][_slice]['ramps']:
			for _matched_slice in get_slices_at_z(z):
				if _matched_slice['map'][x][y]:
					if not _matched_slice['map'][x][y] in WORLD_INFO['slices'][_slice]['neighbors']:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]]= [(x, y)]
					elif not (x, y) in WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]]:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]].append((x, y))
		
		for neighbor in WORLD_INFO['slices'][_slice]['neighbors']:
			print '\tNeighbor:', neighbor, '(%s ramps)' % len(WORLD_INFO['slices'][_slice]['neighbors'][neighbor])