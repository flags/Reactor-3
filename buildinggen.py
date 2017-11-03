from globals import WORLD_INFO

import random


def walker(chunk_key, steps, building_chunks, add_first=False, chunk_keys=True, avoid_chunk_keys=[]):
	_pos = [int(i) for i in chunk_key.split(',')]
	_path = []
	
	if add_first:
		_path.append(_pos[:])
	
	for i in range(steps-add_first):
		_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
		_valid_directions = []
		
		for mod in _directions:
			_n_pos = (_pos[0]+(mod[0]*WORLD_INFO['chunk_size']), _pos[1]+(mod[1]*WORLD_INFO['chunk_size']))
			_n_chunk_key = '%s,%s' % (_n_pos[0], _n_pos[1])
			
			if not _n_chunk_key in building_chunks:
				continue
			
			if _n_chunk_key in avoid_chunk_keys or _n_chunk_key in ['%s,%s' % (p[0], p[1]) for p in _path]:
				continue
			
			_valid_directions.append(mod[:])
		
		if not _valid_directions:
			break
		
		_mod = random.choice(_valid_directions)
		_pos[0] += _mod[0]*WORLD_INFO['chunk_size']
		_pos[1] += _mod[1]*WORLD_INFO['chunk_size']
		_path.append(_pos[:])
	
	if chunk_keys:
		return ['%s,%s' % (p[0], p[1]) for p in _path]
	else:
		return _path

def get_neighbors(chunk_key, only_chunk_keys=[], avoid_chunk_keys=[]):
	_neighbors = []
	_pos = [int(i) for i in chunk_key.split(',')]
	
	for pos in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
		_chunk_key = '%s,%s' % (_pos[0]+(pos[0]*WORLD_INFO['chunk_size']), _pos[1]+(pos[1]*WORLD_INFO['chunk_size']))
		
		if only_chunk_keys and not _chunk_key in only_chunk_keys:
			continue
		
		if _chunk_key in avoid_chunk_keys:
			continue
		
		_neighbors.append(_chunk_key)
	
	return _neighbors

def connect_to_chunks(connect_to, existing_connections, steps, building_chunks):
	_connect_layers = {}
	_all_chunk_keys = []
	
	for room_name in existing_connections:
		for chunk_key in existing_connections[room_name]['chunk_keys']:
			_all_chunk_keys.append(chunk_key)
	
	_allowed = False
	for room_name in connect_to:
		if not room_name in existing_connections:
			continue
		
		_neighbors = []
		for chunk_key in existing_connections[room_name]['chunk_keys']:
			_temp_neighbors = get_neighbors(chunk_key, only_chunk_keys=building_chunks, avoid_chunk_keys=_all_chunk_keys)
			
			if not _temp_neighbors:
				return -1
			
			_neighbors.extend(_temp_neighbors)
		
		_connect_layers[room_name] = {'chunk_keys': existing_connections[room_name]['chunk_keys'],
		                              'neighbors': _neighbors}
		
		if _neighbors:
			_allowed = True
	
	if not _allowed:
		return -1
	
	_common_neighbors = {}
	_highest = 0
	for layer in _connect_layers.values():
		for chunk_key in layer['neighbors']:
			if chunk_key in _common_neighbors:
				_common_neighbors[chunk_key] += 1
			else:
				_common_neighbors[chunk_key] = 1
			
			if _common_neighbors[chunk_key]>_highest:
				_highest = _common_neighbors[chunk_key]

	for chunk_key in _common_neighbors.keys():
		if _common_neighbors[chunk_key]<_highest:
			del _common_neighbors[chunk_key]
	
	if not _common_neighbors:
		return False
	
	if _highest<len(_connect_layers):
		return -1
	
	return random.choice(_common_neighbors.keys())

def _create_building(chunk_key, design, building_chunks):
	_pos = chunk_key
	_rooms = {}
	_building = {'rooms': {}}
	
	if 'flags' in design:
		_building['flags'] = design['flags']
	else:
		_building['flags'] = {}
	
	_building_chunk_keys = []
	_build_queue = [design['build_order']]
	_to_build = design['chunks'].keys()
	
	while _build_queue:
		_room_name = _build_queue.pop(0)
		_to_build.remove(_room_name)
		_building['rooms'][_room_name] = {'chunk_keys': []}
		_room = design['chunks'][_room_name]
		
		if 'flags' in _room:
			_flags = _room['flags']
		else:
			_flags = {}
		
		if _rooms:
			_start_chunk = connect_to_chunks(_room['doors'], _building['rooms'], _room['chunks'], building_chunks)
			
			if not _start_chunk:
				return False
			
			if _start_chunk == -1:
				return -1
			
			_path = walker(_start_chunk, _room['chunks'], building_chunks, avoid_chunk_keys=_building_chunk_keys, add_first=True)
			_rooms[_room_name] = _path[:]
			_building['rooms'][_room_name] = {'chunk_keys': _rooms[_room_name],
			                         'type': _room['type'],
			                         'floor': _room['floor'],
			                         'walls': _room['walls'],
			                         'doors': _room['doors'],
			                         'no_doors': [],
			                         'items': _room['items'],
			                         'flags': _flags,
			                         'spawns': {'away_from_door': [],
			                                    'door': [],
			                                    'middle': [],
			                                    'floor': [],
			                                    'edge': []}}
			_building_chunk_keys.extend(_rooms[_room_name])
		else:
			_rooms[_room_name] = walker(_pos, _room['chunks'], building_chunks, avoid_chunk_keys=_building_chunk_keys, add_first=True)
			_building_chunk_keys.extend(_rooms[_room_name])
			_building['rooms'][_room_name] = {'chunk_keys': _rooms[_room_name],
			                         'type': _room['type'],
			                         'floor': _room['floor'],
			                         'walls': _room['walls'],
			                         'doors': _room['doors'],
			                         'no_doors': [],
			                         'items': _room['items'],
			                         'flags': _flags,
			                         'spawns': {'away_from_door': [],
			                                    'door': [],
			                                    'middle': [],
			                                    'floor': [],
			                                    'edge': []}}
		
		if _room['doors']:
			_build_queue.extend([d for d in _room['doors'] if d in _to_build and not d in _build_queue])
	
	return _building

def create_building(chunk_key, design, building_chunks):
	_building = None
	
	while not _building:
		_building = _create_building(chunk_key, design, building_chunks)
	
	if _building == -1:
		return False
	
	return _building
