def old_light(los_map, world_pos, size, row, start_slope, end_slope, xx, xy, yx, yy, collision_map, map_size):
	_return_chunks = set()
	
	if start_slope < end_slope:
		return los_map, _return_chunks

	x, y, z = world_pos

	_next_start_slope = start_slope

	for i in range(row, size):
		_blocked = False
	
		_d_x = -i
		_d_y = -i
		while _d_x <= 0:
			_l_slope = (_d_x - 0.5) / (_d_y + 0.5)
			_r_slope = (_d_x + 0.5) / (_d_y - 0.5)
	
			if start_slope < _r_slope:
				_d_x += 1
				continue
			elif end_slope>_l_slope:
				break
		
			_sax = _d_x * xx + _d_y * xy
			_say = _d_x * yx + _d_y * yy
		
			if (_sax<0 and abs(_sax)>x) or (_say<0 and abs(_say)>y):
				_d_x += 1
				continue
		
			_a_x = x + _sax
			_a_y = y + _say
		
			if _a_x >= map_size[0] or _a_y >= map_size[1]:
				_d_x += 1
				continue
		
			_rad2 = size*size
			_solid = collision_map[_sax+size, _say+size]
		
			if (_d_x * _d_x + _d_y * _d_y) < _rad2:
				los_map[_sax+size, _say+size] = 1
		
			if not _solid:
				_chunk_key = '%s,%s' % ((_a_x/5)*5, (_a_y/5)*5)
		
				if not _chunk_key in _return_chunks:
					_return_chunks.add(_chunk_key)
		
			if _blocked:
				if _solid:
					_next_start_slope = _r_slope
					_d_x += 1
					continue
				else:
					_blocked = False
					start_slope = _next_start_slope
			elif _solid:
				_blocked = True
				_next_start_slope = _r_slope
				_map, _chunk_keys = old_light(los_map, world_pos, size, i+1, start_slope, _l_slope, xx, xy, yx, yy, collision_map, map_size)
				
				los_map += _map
				_return_chunks.update(_chunk_keys)
		
			_d_x += 1
			
			if _blocked:
				break
	
	return los_map, _return_chunks