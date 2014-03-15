WORLD_INFO = {'chunk_size': 5}


import random


#TODO: Replace?
def walker(chunk_key, steps, add_first=False, chunk_keys=True, avoid_chunk_keys=[]):
	_pos = [int(i) for i in chunk_key.split(',')]
	_path = []
	
	if add_first:
		_path.append(_pos)
	
	for i in range(steps-add_first):
		_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
		_valid_directions = []
		
		for mod in _directions:
			_n_pos = (_pos[0]+(mod[0]*WORLD_INFO['chunk_size']), _pos[1]+(mod[1]*WORLD_INFO['chunk_size']))
			_n_chunk_key = '%s,%s' % (_n_pos[0], _n_pos[1])
			
			if _n_chunk_key in avoid_chunk_keys or _n_chunk_key in ['%s,%s' % (p[0], p[1]) for p in _path]:
				continue
			
			_valid_directions.append(mod)
		
		if not _valid_directions:
			print 'Take a break...'
			
			break
		
		_mod = random.choice(_valid_directions)
		_pos[0] += _mod[0]*WORLD_INFO['chunk_size']
		_pos[1] += _mod[1]*WORLD_INFO['chunk_size']
		_path.append(_pos[:])
	
	if chunk_keys:
		return ['%s,%s' % (p[0], p[1]) for p in _path]
	else:
		return _path

def find_best_offshoot_chunk_key(chunk_keys, occupied_chunk_keys, steps):
	_avoid_chunk_keys = occupied_chunk_keys[:]
	_avoid_chunk_keys.append(chunk_keys)
	_results = []
	
	for chunk_key in chunk_keys:
		_path = walker(chunk_key, steps, avoid_chunk_keys=occupied_chunk_keys)
		
		if len(_path) == steps:
			_results.append(_path)
	
	return random.choice(_results)

def create_building(chunk_key, design):
	#TODO: Replace
	_pos = chunk_key
	_rooms = {}
	_building_chunk_keys = []
	_to_design = design['build_order']
	_room_name = _to_design[0]
	
	while _to_design:
		print _room_name
		_to_design.remove(_room_name)
		
		_room = design['chunks'][_room_name]
		
		if _rooms:			
			_path = find_best_offshoot_chunk_key(_rooms[_rooms.keys()[len(_rooms)-1]], _building_chunk_keys, _room['chunks'])
			_rooms[_room_name] = _path
			
			for pos in _path:
				if _path.count(pos) == 2:
					print 'ESCAPE'
			
			_building_chunk_keys.extend(_rooms[_room_name])
		else:	
			_rooms[_room_name] = walker(_pos, _room['chunks'], add_first=not len(_rooms))
			_building_chunk_keys.extend(_rooms[_room_name])
			
			for pos in _rooms[_room_name]:
				if _rooms[_room_name].count(pos) == 2:
					print 'ESCAPE'
		
		#_set_new_room = False
		
		#Nothing weird going on here, I promise!
		#while _room['doors']:
		#	_next_room_name = _room['doors'].pop()
		#	
		#	if _next_room_name in _to_design:
		#		_room_name = _next_room_name
		#		_set_new_room = True
		#		break
		#
		#if not _set_new_room and _to_design:
		if _to_design:
			_room_name = _to_design[0]
	
	print _rooms
	
	return _building_chunk_keys

_test = {'chunks': {'shopping': {'type': 'interior',
                                  'chunks': 3,
                                  'doors': ['parking lot', 'office']},
                     'checkout': {'type': 'interior',
                                  'chunks': 1,
                                  'doors': []},
                     'office': {'type': 'interior',
                                'chunks': 2,
                                'doors': ['shopping']},
                     'parking lot': {'type': 'interior',
                                     'chunks': 3,
                                     'doors': ['shopping']}},
         'build_order': ['shopping', 'checkout', 'office', 'parking lot']}

_building = create_building('25,25', _test)
_rooms = 0

for y in range(5, 50, WORLD_INFO['chunk_size']):
	for x in range(5, 50, WORLD_INFO['chunk_size']):
		_chunk_key = '%s,%s' % (x, y)
		
		if _chunk_key in _building:
			_rooms += 1
			print 'X',
		else:
			print '.',
	
	print

print _rooms