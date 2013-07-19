import time
import sys

MAP_SIZE = (20, 20, 4)
WORLD_INFO = {'zoneid': 0, 'slices': {}, 'map': []}

# Slice map key
# -1  - 
# 0   - Clear (shouldn't see this)
# >=1 - Slice id

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

WORLD_INFO['map'].extend(create_map_array())

def draw_map(source_map, z):
	for x in range(MAP_SIZE[0]):
		for y in range(MAP_SIZE[1]):
			if source_map[x][y][z]:
				print '#',
			else:
				print '.',
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
			elif not slice_map[x][y]:
				print '.',
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
			if not WORLD_INFO['map'][x][y][z]:
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
					if z < MAP_SIZE[2]-1 and WORLD_INFO['map'][x][y][z+1]:
						if z < MAP_SIZE[2]-2 and WORLD_INFO['map'][x][y][z+2]:
							pass
						else:
							_slice[x][y] = -1
					
					if not _slice[x][y] == _z_id:
						continue
					
					for x_mod,y_mod in [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]:
						_x = x+x_mod
						_y = y+y_mod
						
						if _x<0 or _x>=MAP_SIZE[0] or _y<0 or _y>=MAP_SIZE[1]:
							continue
						
						if WORLD_INFO['map'][_x][_y][z] and not (_slice[_x][_y] == _z_id or _slice[_x][_y] == -1):
							_slice[_x][_y] = _z_id
							_changed = True
						
						#Above, Below
						if z < MAP_SIZE[2]-1 and WORLD_INFO['map'][_x][_y][z+1]:
							if z < MAP_SIZE[2]-2 and WORLD_INFO['map'][_x][_y][z+2]:
								pass
							else:
								_ramps.append((_x, _y, z+1))
								continue
						
						if z and not WORLD_INFO['map'][_x][_y][z] and WORLD_INFO['map'][_x][_y][z-1]:
							_ramps.append((_x, _y, z-1))
	
		WORLD_INFO['slices'][_z_id] = {'z': z, 'id': _z_id, 'map': _slice, 'ramps': _ramps, 'neighbors': {}}
		
		if 'ramp' in sys.argv:
			draw_ramps(_ramps)
			print

def get_slices_at_z(z):
	return [s for s in WORLD_INFO['slices'].values() if s['z'] == z]

def can_path_to_zone(z1, z2):
	if z1 == z2:
		return True
	
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

def create_zone_map():
	for z in range(MAP_SIZE[2]):
		_stime = time.time()
		process_slice(z)
		print time.time()-_stime

def connect_ramps():
	for _slice in WORLD_INFO['slices']:
		for x,y,z in WORLD_INFO['slices'][_slice]['ramps']:
			for _matched_slice in get_slices_at_z(z):
				if _matched_slice['map'][x][y]>0:
					if not _matched_slice['map'][x][y] in WORLD_INFO['slices'][_slice]['neighbors']:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]] = [(x, y)]
					elif not (x, y) in WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]]:
						WORLD_INFO['slices'][_slice]['neighbors'][_matched_slice['map'][x][y]].append((x, y))
						
	for _slice in WORLD_INFO['slices']:
		print 'Zone %s' % _slice, '@ z-level',WORLD_INFO['slices'][_slice]['z']
		for neighbor in WORLD_INFO['slices'][_slice]['neighbors']:
			print '\tNeighbor:', neighbor, '(%s ramps)' % len(WORLD_INFO['slices'][_slice]['neighbors'][neighbor])
		
		#print WORLD_INFO['slices'][_slice]['neighbors'].keys()
		
		if not WORLD_INFO['slices'][_slice]['neighbors']:
			print '\tNo neighbors.'

if __name__ == '__main__':
	create_zone_map()
	print
	connect_ramps()
	print can_path_to_zone(1, 1)