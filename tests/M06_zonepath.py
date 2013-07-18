import time
import sys

MAP_SIZE = (20, 20, 3)
SLICES = {}
MAP = []
WORLD_INFO = {'zoneid': 0, 'slices': SLICES, 'map': MAP}

def create_map_array(flat=False):
	_map = []
	for x in range(MAP_SIZE[0]):
		_y = []
		
		for y in range(MAP_SIZE[1]):
			_z = []
			
			if flat:
				_y.append(0)
			else:
				for z in range(MAP_SIZE[2]):
					if (y >= 5 and x >= 10 and not x==15) and z == 1:
						_z.append(1)
					elif (y < 5 or x < 10 or x == 15) and not z:
						_z.append(1)
					elif (y >= 8 and x >= 16) and z == 2:
						_z.append(1)
					elif (y >= 9 and x >= 17) and z == 3 and not x == 18:
						_z.append(1)
					else:
						_z.append(0)
				
				_y.append(_z)
		
		_map.append(_y)
	
	return _map

MAP.extend(create_map_array())

def draw_map(source_map, z):
	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			print source_map[x][y][z],
		
		print

def draw_slice(slice_map):
	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			if slice_map[x][y] == -1:
				print '^',
			elif slice_map[x][y] == -2:
				print 'v',
			elif slice_map[x][y] == -3:
				print ' '
			else:
				print slice_map[x][y],
		
		print

def draw_ramps(ramps):
	_ramps = [r[:2] for r in ramps]
	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			if (x, y) in _ramps:
				print '^',
			else:
				print '.',
		
		print

def get_unzoned(slice_map, z):
	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			if not MAP[x][y][z]:
				continue
			
			if slice_map[x][y]>0 or slice_map[x][y] <= -1:
				continue
			
			if not slice_map[x][y]:
				return x,y
	
	return None

def process_slice(z):
	print 'Processing:',z
	_runs = 0
	_slice = create_map_array(flat=True)
	
	while 1:
		WORLD_INFO['zoneid'] += 1
		_z_id = WORLD_INFO['zoneid']
		_ramps = []
		_start_pos = get_unzoned(_slice, z)
		
		if not _start_pos:
			if 'slice' in sys.argv:
				draw_slice(_slice)
			
			if 'map' in sys.argv:
				draw_map(MAP, z)
			
			print '\tRuns:',_runs,'Time:',
			break
		
		_slice[_start_pos[0]][_start_pos[1]] = _z_id
		
		_changed = True
		while _changed:
			_runs += 1
			_changed = False
			
			for x in range(MAP_SIZE[0]):
				for y in range(MAP_SIZE[1]):
					if z < MAP_SIZE[2]-1 and MAP[x][y][z+1]:
						_slice[x][y] = -1
					#elif z >= 2 and not MAP[x][y][z-1] and not MAP[x][y][z-2]:
					#	_slice[x][y] = -2
					
					if not _slice[x][y] == _z_id:
						continue
					
					for x_mod,y_mod in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
						_x = x+x_mod
						_y = y+y_mod
						
						if _x<0 or _x>=MAP_SIZE[0] or _y<0 or _y>=MAP_SIZE[1]:
							continue
						
						#if _slice[_x][_y] <= -1:
						#	continue
						
						if MAP[_x][_y][z] and not _slice[_x][_y] == _z_id:
							_slice[_x][_y] = _z_id
							_changed = True
							
						#Below
						if z and not MAP[_x][_y][z] and MAP[_x][_y][z-1]:
							_ramps.append((_x, _y, z-1))
						
						#Above
						if z < MAP_SIZE[2]-1 and MAP[_x][_y][z+1]:
							if z < MAP_SIZE[2]-2 and MAP[_x][_y][z+2]:
								pass
							else:
								_ramps.append((_x, _y, z-1))
								
						#if z < MAP_SIZE[2]-2 and MAP[_x][_y][z+2]:
						#	continue
						#if z < MAP_SIZE[2]-1 and MAP[_x][_y][z+1]:
						#	_ramps.append((_x, _y, z+1))
						#if not MAP[_x][_y][z] and z and MAP[_x][_y][z-1]:
						#	_ramps.append((_x, _y, z-1))
	
		SLICES[_z_id] = {'z': z, 'id': _z_id, 'map': _slice, 'ramps': _ramps, 'neighbors': {}}
		
		if 'ramp' in sys.argv:
			draw_ramps(_ramps)
			print

def get_slices_at_z(z):
	return [s for s in SLICES.values() if s['z'] == z]

def can_path_to_zone(z1, z2):
	_checked = []
	_to_check = [z1]
	
	while _to_check:
		_checking = _to_check.pop()
		_checked.append(_checking)
		
		_to_check.extend([n for n in WORLD_INFO['slices'][_checking]['neighbors'] if not n in _checked])
		
		if z2 in _to_check:
			_checked.append(z2)
			print _checked
			return True
	
	return False

def can_path_to_zone_old(z1, z2, checked=[], path=[]):
	z1 = int(z1)
	z2 = int(z2)
	
	path.append(z1)
	if z1 == z2:
		#path.append(z1)
		return True
	
	#if not path:
	#	path.append(z1)
	
	checked.append(z1)
	#print checked
	
	if z2 in SLICES[z1]['neighbors']:
		path.append(z2)
		return path
	
	_neighbors = [n for n in SLICES[z1]['neighbors'] if not n in checked]
	
	if not _neighbors:
		return False
	
	for _neighbor in _neighbors:
		_zone = can_path_to_zone(_neighbor, z2, checked=checked, path=path)
		if _zone:
			return path
		
	
	return False

def create_zone_map():
	for z in range(MAP_SIZE[2]):
		_stime = time.time()
		process_slice(z)
		print time.time()-_stime

def connect_ramps():
	for _slice in SLICES:
		#print 'Connecting:','Zone %s' % _slice, '@ z-level',SLICES[_slice]['z']
		for x,y,z in SLICES[_slice]['ramps']:
			for _matched_slice in get_slices_at_z(z):
				if _matched_slice['id'] == _slice:
					continue
				
				if _matched_slice['map'][x][y]>0:
					if not _matched_slice['map'][x][y] in SLICES[_slice]['neighbors']:
						SLICES[_slice]['neighbors'][_matched_slice['map'][x][y]] = [(x, y)]
					elif not (x, y) in SLICES[_slice]['neighbors'][_matched_slice['map'][x][y]]:
						SLICES[_slice]['neighbors'][_matched_slice['map'][x][y]].append((x, y))
				
					#if not _slice in _matched_slice['neighbors']:
					#	_matched_slice['neighbors'][_slice] = [(x, y)]
					#elif not (x, y) in _matched_slice['neighbors'][_slice]:
					#	_matched_slice['neighbors'][_slice].append((x, y))
						
	for _slice in SLICES:
		pass
		#print 'Zone %s' % _slice, '@ z-level',SLICES[_slice]['z']
		#for neighbor in SLICES[_slice]['neighbors']:
		#	print '\tNeighbor:', neighbor, '(%s ramps)' % len(SLICES[_slice]['neighbors'][neighbor])
		
		#print SLICES[_slice]['neighbors'].keys()
		
		#if not SLICES[_slice]['neighbors']:
		#	print '\tNo neighbors.'

if __name__ == '__main__':
	create_zone_map()
	print
	connect_ramps()
	#print can_path_to_zone(3, 9)