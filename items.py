from globals import *

import graphics as gfx

import scripting
import maputils
import drawing
import numbers
import effects
import timers
import alife
import logic
import zones
import maps
import life

import logging
import random

try:
	import ujson as json
except:
	import json

def load_item(item):
	with open(os.path.join(ITEM_DIR, item),'r') as e:
		try:
			logging.debug('Caching item: %s' % item)
			return json.loads(''.join(e.readlines()))
		except ValueError,e:
			raise Exception('Failed to load item: %s' % e)

def initiate_all_items():
	logging.debug('Loading all items...')
	for (dirpath, dirname, filenames) in os.walk(ITEM_DIR):
		for f in [f for f in filenames if f.count('.json')]:
			initiate_item(f)

def initiate_item(name):
	"""Loads (and returns) new item type into memory."""
	if name in ITEM_TYPES:
		logging.warning('Item type \'%s\' is already loaded. Reloading...' % name)
	
	item = load_item(name)
	_marked_for_reint = {}
	
	if not 'prefix' in item:
		logging.warning('No prefix set for item type \'%s\'. Using default (%s).' % (name, DEFAULT_ITEM_PREFIX))
		item['prefix'] = DEFAULT_ITEM_PREFIX
	
	if not 'icon' in item:
		logging.warning('No icon set for item type \'%s\'. Using default (%s).' % (name, DEFAULT_ITEM_ICON))
		item['icon'] = DEFAULT_ITEM_ICON
	elif isinstance(item['icon'], int):
		item['icon'] = chr(item['icon'])
	
	if not 'color' in item:
		item['color'] = (tcod.white, None)
	else:
		_fore = None
		_back = None
		
		if item['color'][0]:
			_fore = tcod.Color(item['color'][0][0], item['color'][0][1], item['color'][0][2])
		
		if item['color'][1]:
			_back = tcod.Color(item['color'][1][0], item['color'][1][1], item['color'][1][2])
		
		item['color'] = (_fore, _back)
	
	if not 'flags' in item:
		logging.error('No flags set for item type \'%s\'. Errors may occur.' % name)
		item['flags'] = ''
	
	if 'attaches_to' in item:
		item['attaches_to'] = item['attaches_to'].split('|')
	
	if 'capacity' in item:
		item['max_capacity'] = [int(c) for c in item['capacity'].split('x')]
		item['max_capacity'] = item['max_capacity'][0]*item['max_capacity'][1]
		item['capacity'] = 0
		item['storing'] = []
	
	if not 'size' in item:
		logging.warning('No size set for item type \'%s\'. Using default (%s).' % (name, DEFAULT_ITEM_SIZE))
		item['size'] = DEFAULT_ITEM_SIZE
	
	if item['type'] == 'gun':
		item[item['feed']] = None
	
	#item['flags'] = []
	_flags = {}
	for flag in item['flags'].split('|'):
		if '=' in flag:
			_flag_split = flag.split('=')
			_flags[_flag_split[0]] = None
			
			if len(_flag_split)==2:
				_flags[_flag_split[0]] = _flag_split[1]
		elif '[' in flag:
			_ocount = flag.count('[')
			_ccount = flag.count(']')
			
			if _ocount > _ccount:
				logging.error('Brace mismatch in item \'%s\': Expected \']\'' % name)
				continue
			elif _ocount < _ccount:
				logging.error('Brace mismatch in item \'%s\': Expected \'[\'' % name)
				continue
			
			_flags[flag.split('[')[0]] = scripting.initiate(item, flag)
		else:
			_flags[flag] = None
		
	if 'CAN_BURN' in _flags:
		item['burning'] = 0
		item['burnt'] = False
	
	item['flags'] = _flags
	item['size'] = [int(c) for c in item['size'].split('x')]
	item['size'] = item['size'][0]*item['size'][1]
	
	for key in item:
		if isinstance(item[key],list):
			_marked_for_reint[key] = item[key][:]
	
	item['marked_for_reint'] = _marked_for_reint.copy()
	
	#Unicode isn't handled all that well on Windows for some reason...
	for key in item:
		_value = item[key]
		del item[key]
		item[str(key)] = _value
		
		if isinstance(item[key],unicode):
			item[key] = str(item[key])
	
	ITEM_TYPES[item['name']] = item
	
	return item

def create_item(name, position=[0,0,2], item=None):
	"""Initiates and returns a copy of an item type."""
	if not item:
		item = ITEM_TYPES[name].copy()
	
	if 'marked_for_reint' in item:
		for key in item['marked_for_reint']:
			item[key] = item['marked_for_reint'][key][:]
		
		del item['marked_for_reint']

	item['uid'] = str(WORLD_INFO['itemid'])
	item['pos'] = list(position)
	item['realpos'] = list(position)
	item['velocity'] = [0.0, 0.0, 0.0]
	item['friction'] = 0
	item['gravity'] = WORLD_INFO['world gravity']
	item['lock'] = None
	item['owner'] = None
	item['aim_at_limb'] = None
	
	if not 'examine_keys' in item:
		item['examine_keys'] = ['description']
	
	if 'speed' in item:
		item['max_speed'] = item['speed']
	else:
		item['max_speed'] = 2
	
	add_to_chunk(item)
	ITEMS[item['uid']] = item
	
	WORLD_INFO['itemid'] += 1
	return item['uid']

def delete_item(item):
	logging.debug('Deleting references to item %s' % item['uid'])
	
	for life in [LIFE[i] for i in LIFE]:
		if item['uid'] in life['know_items']:
			alife.brain.offload_remembered_item(life, item['uid'])
			alife.survival.remove_item_from_needs(life, item['uid'])
			del life['know_items'][item['uid']]
			
			logging.debug('\tDeleted reference in life #%s' % life['id'])
	
	timers.remove_by_owner(item)
	remove_from_chunk(item)
	
	if gfx.position_is_in_frame(item['pos']):
		gfx.refresh_window_position(item['pos'][0]-CAMERA_POS[0], item['pos'][1]-CAMERA_POS[1])
	
	del ITEMS[item['uid']]

def add_to_chunk(item):
	_chunk = alife.chunks.get_chunk(alife.chunks.get_chunk_key_at(item['pos']))
	
	if not item['uid'] in _chunk['items']:
		_chunk['items'].append(item['uid'])

def remove_from_chunk(item):
	_chunk = alife.chunks.get_chunk(alife.chunks.get_chunk_key_at(item['pos']))
	
	if item['uid'] in _chunk['items']:
		_chunk['items'].remove(item['uid'])

def save_all_items():
	for item in ITEMS.values():
		if isinstance(item['icon'], unicode) or isinstance(item['icon'], str):
			item['icon'] = ord(item['icon'][0])
		
		_fore = None
		_back = None
		
		if item['color'][0]:
			_fore = (item['color'][0][0], item['color'][0][1], item['color'][0][2])
		
		if item['color'][1]:
			_back = (item['color'][1][0], item['color'][1][1], item['color'][1][2])
		
		item['color'] = (_fore, _back)

def reload_all_items():
	for item in ITEMS.values():
		if not isinstance(item['icon'], unicode) and not isinstance(item['icon'], str):
			item['icon'] = chr(item['icon'])
		
		if item['color'][0]:
			_fore = tcod.Color(item['color'][0][0], item['color'][0][1], item['color'][0][2])
		else:
			_fore = tcod.white
		
		if item['color'][1]:
			_back = tcod.Color(item['color'][1][0], item['color'][1][1], item['color'][1][2])
		else:
			_back = None
		
		item['color'] = (_fore, _back)

def get_item_from_uid(uid):
	"""Helper function. Returns item of `uid`."""
	return ITEMS[uid]

def get_pos(item_uid):
	item = ITEMS[item_uid]
	
	if 'parent_id' in item:
		return LIFE[item['parent_id']]['pos']
	
	return item['pos']

def get_items_at(position):
	"""Returns list of all items at a given position."""
	_items = []
	
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if is_item_owned(_item):
			continue
		
		if tuple(item['pos']) == tuple(position):
			_items.append(item)
	
	return _items

def get_name(item):
	"""Returns the full name of an item."""
	_prefixes = [item['prefix']]
	
	if 'burning' in item:
		if item['burning']:
			_prefixes.append('burning')
		elif item['burnt']:
			_prefixes.append('burnt')
	
	if 'capacity' in item:
		_score = item['capacity']/float(item['max_capacity'])
		
		if _score >= .75:
			_prefixes.append('nearly full')
		elif _score == 0:
			_prefixes.append('empty')
	
	if len(_prefixes)>=2:
		if _prefixes[0] == 'a' and _prefixes[1] in ['empty']:
			_prefixes[0] = 'an'
	
	return '%s %s' % (' '.join(_prefixes), item['name'])		

def move(item, direction, speed, friction=0.05, _velocity=0):
	"""Sets new velocity for an item. Returns nothing."""
	velocity = numbers.velocity(direction, speed)
	velocity[2] = _velocity
	
	item['friction'] = friction
	item['velocity'] = velocity
	item['realpos'] = item['pos'][:]
	
	logging.debug('%s flies off in an arc! (%s)' % (get_name(item), item['velocity']))

def is_item_owned(item_uid):
	_item = get_item_from_uid(item_uid)
	
	if _item.has_key('parent_id'):
		return True
	
	if _item.has_key('parent'):
		return True
	
	if _item.has_key('stored_in'):
		return True
	
	return False

def draw_items():
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if is_item_owned(item['uid']):
			continue
		
		if item['pos'][0] >= CAMERA_POS[0] and item['pos'][0] < CAMERA_POS[0]+MAP_WINDOW_SIZE[0] and\
			item['pos'][1] >= CAMERA_POS[1] and item['pos'][1] < CAMERA_POS[1]+MAP_WINDOW_SIZE[1]:
			_x = item['pos'][0] - CAMERA_POS[0]
			_y = item['pos'][1] - CAMERA_POS[1]
		
			if not LOS_BUFFER[0][_y,_x]:
				continue
			
			gfx.blit_char(_x,
				_y,
				item['icon'],
				item['color'][0],
				item['color'][1],
				char_buffer=MAP_CHAR_BUFFER,
				rgb_fore_buffer=MAP_RGB_FORE_BUFFER,
				rgb_back_buffer=MAP_RGB_BACK_BUFFER)

def update_container_capacity(container_uid):
	"""Updates the current capacity of container. Returns nothing."""
	_container = get_item_from_uid(container_uid)
	_capacity = 0
	
	for item in _container['storing']:
		_capacity += get_item_from_uid(item)['size']
	
	_container['capacity'] = _capacity

def can_store_item_in(item_uid, container_uid):
	_item = get_item_from_uid(item_uid)
	_container = get_item_from_uid(container_uid)
	
	if 'max_capacity' in _container and _container['capacity']+_item['size'] <= _container['max_capacity']:
		return container_uid
		
	return False

def store_item_in(item_uid, container_uid):
	if not can_store_item_in(item_uid, container_uid):
		print 'cannot store in'
		raise Exception('Cant store item %s in container %s: %s is full.' % (item_uid, container_uid, ITEMS[container_uid]['name']))
	
	_item = get_item_from_uid(item_uid)
	
	_container = get_item_from_uid(container_uid)
	_container['storing'].append(item_uid)
	_container['capacity'] += _item['size']
	_item['stored_in'] = container_uid
	
	update_container_capacity(container_uid)
	add_to_chunk(_item)
	return True

def remove_item_from_any_storage(item_uid):
	_item = get_item_from_uid(item_uid)
	
	_container = get_item_from_uid(_item['stored_in'])
	_container['storing'].remove(item_uid)
	update_container_capacity(_item['stored_in'])
	
	del _item['stored_in']

def burn(item, amount):
	if not 'CAN_BURN' in item['flags']:
		return False
	
	item['burning'] += amount*.1

	if item['owner']:
		logging.debug('%s\'s %s catches fire!' % (' '.join(LIFE[item['owner']]['name']), item['name']))
		
		if 'player' in LIFE[item['owner']]:
			gfx.message('Your %s catches fire!' % item['name'])

def explode(item):
	if not item['type'] == 'explosive':
		return False
	
	effects.create_light(item['pos'], (255, 255, 255), item['damage']['force']*2, 0, fade=0.8)
	
	if alife.sight.can_see_position(LIFE[SETTINGS['controlling']], item['pos']):
		gfx.message('%s explodes!' % get_name(item))
		logic.show_event('%s explodes!' % get_name(item), item=item, delay=0)
		
	#elif numbers.distance(
	
	#TODO: Dirty hack
	for life_id in LIFE:
		_force = numbers.clip((item['damage']['force']*2)-numbers.distance(LIFE[life_id]['pos'], item['pos']), 0, 100)
		
		if not _force:
			continue
		
		_known_item = alife.brain.remembers_item(LIFE[life_id], item)
		_direction = numbers.direction_to(item['pos'], LIFE[life_id]['pos'])
		
		#TODO: Intelligent(?) limb groups?
		_distance = numbers.distance(LIFE[life_id]['pos'], item['pos'])/2
		#_limbs = random.sample(LIFE[life_id]['body'].keys(), _force-_distance)
		_limb = random.choice(LIFE[life_id]['body'].keys())
		
		#ex: memory(life, 'shot at by (missed)', target=item['owner'], danger=3, trust=-10)
		print 'known item', _known_item
		if _known_item and _known_item['last_seen_time'] < 100 and _known_item['last_owned_by']:
			life.memory(LIFE[life_id], 'blown_up_by', target=_known_item['last_owned_by'], trust=-10, danger=3)
		
		#for _limb in _limbs:
		life.add_wound(LIFE[life_id], _limb, force_velocity=numbers.velocity(_direction, _force))
		
		life.push(LIFE[life_id], _direction, _force)
		
		if 'player' in LIFE[life_id]:
			life.say(LIFE[life_id], '@n are thrown by the explosion!', action=True)
		else:
			life.say(LIFE[life_id], '@n is thrown by the explosion!', action=True)
	
	if 'fire' in item['damage']:
		_circle = drawing.draw_circle(item['pos'], item['radius'])
		_zone = zones.get_zone_at_coords(item['pos'])
		
		if _zone:	
			for pos in zones.dijkstra_map(item['pos'], [item['pos']], [_zone], return_score_in_range=[0, item['damage']['fire']]):
				if not pos in _circle:
					continue
				
				if not maps.position_is_in_map(pos):
					continue
				
				for life_id in LIFE_MAP[pos[0]][pos[1]]:
					for _visible_item in [get_item_from_uid(i) for i in life.get_all_visible_items(LIFE[life_id])]:
						if not 'CAN_BURN' in _visible_item['flags']:
							continue
						
						burn(_visible_item, item['damage']['fire'])
				
				if not random.randint(0, 4):
					effects.create_fire((pos[0], pos[1], item['pos'][2]), intensity=item['damage']['fire'])
			
				_dist = numbers.distance(item['pos'], pos)/2
				if not random.randint(0, _dist) or not _dist:
					effects.create_ash(pos)
		
				if gfx.position_is_in_frame(pos):
					_render_pos = gfx.get_render_position(pos)
					gfx.refresh_window_position(_render_pos[0], _render_pos[1])
	
	delete_item(item)

def collision_with_solid(item, pos):
	if pos[0]<0 or pos[0]>=MAP_SIZE[0] or pos[1]<0 or pos[1]>=MAP_SIZE[1]:
		return True
	
	if WORLD_INFO['map'][pos[0]][pos[1]][pos[2]] and item['velocity'][2]<0:
		#TODO: Bounce
		item['velocity'] = [0, 0, 0]
		item['pos'] = pos
		
		return True
	
	if item['velocity'][2]>=0:
		_z = 1
	else:
		_z = -1
	
	if not pos[0]-1 < 0 and item['velocity'][0]<0 and WORLD_INFO['map'][pos[0]-1][pos[1]][pos[2]+_z]:
		item['velocity'][0] = -item['velocity'][0]*.8
	elif not pos[0]+1 >= MAP_SIZE[0]-1 and item['velocity'][0]>0 and WORLD_INFO['map'][pos[0]+1][pos[1]][pos[2]+_z]:
		item['velocity'][0] = -item['velocity'][0]*.8
	
	if not pos[1]-1 < 0 and item['velocity'][1]<0 and WORLD_INFO['map'][pos[0]][pos[1]-1][pos[2]+_z]:
		item['velocity'][1] = -item['velocity'][1]*.8
	elif not pos[1]+1 >= MAP_SIZE[1]-1 and item['velocity'][1]>0 and WORLD_INFO['map'][pos[0]][pos[1]+1][pos[2]+_z]:
		item['velocity'][1] = -item['velocity'][1]*.8
	
	return False

def create_effects(item, pos, real_z_pos, z_min):
	for _z in range(0, 2):
		_z_level = numbers.clip(z_min-_z, 0, maputils.get_map_size(WORLD_INFO['map'])[2]-1)
		
		if WORLD_INFO['map'][pos[0]][pos[1]][_z_level]:
			if int(round(real_z_pos))-_z_level<=2:
				if 'BLOODY' in item['flags']:
					if random.randint(0,50)<=35:
						effects.create_splatter('blood', [pos[0]+random.randint(-2, 2), pos[1]+random.randint(-2, 2), _z_level])
			
				break

def get_min_max_velocity(item):
	if item['velocity'][0]>0:
		_min_x_vel = 0
		_max_x_vel = 255
	else:
		_min_x_vel = -255
		_max_x_vel = 0
	
	if item['velocity'][1]>0:
		_min_y_vel = 0
		_max_y_vel = 255
	else:
		_min_y_vel = -255
		_max_y_vel = 0
	
	return _min_x_vel, _min_y_vel, _max_x_vel, _max_y_vel

def tick_item(item_uid):
	item = ITEMS[item_uid]
	
	if 'CAN_BURN' in item['flags'] and item['burning'] and item['owner']:
		life.burn(LIFE[item['owner']], item['burning'])
	
	_z_max = numbers.clip(item['pos'][2], 0, maputils.get_map_size(WORLD_INFO['map'])[2]-1)
	if item['velocity'][:2] == [0.0, 0.0] and WORLD_INFO['map'][item['pos'][0]][item['pos'][1]][_z_max]:
		return False
	
	_x = item['pos'][0]-CAMERA_POS[0]
	_y = item['pos'][1]-CAMERA_POS[1]
	if 0<=_x<MAP_WINDOW_SIZE[0] and 0<=_y<MAP_WINDOW_SIZE[1]:
		gfx.refresh_window_position(_x, _y)
	
	item['realpos'][0] += item['velocity'][0]
	item['realpos'][1] += item['velocity'][1]
	_break = False
	_line = drawing.diag_line(item['pos'],(int(round(item['realpos'][0])),int(round(item['realpos'][1]))))
	
	if not _line:
		item['velocity'][2] -= item['gravity']
		item['realpos'][2] = item['realpos'][2]+item['velocity'][2]
		item['pos'][2] = int(round(item['realpos'][2]))
		
		if item['pos'][0]<0 or item['pos'][0]>=MAP_SIZE[0] or item['pos'][1]<0 or item['pos'][1]>=MAP_SIZE[1]:
			delete_item(ITEMS[item_uid])
			return False
		
		_z_min = numbers.clip(int(round(item['realpos'][2])), 0, maputils.get_map_size(WORLD_INFO['map'])[2]-1)
		if collision_with_solid(item, [item['pos'][0], item['pos'][1], _z_min]):
			pos = item['pos'][:]
			_break = True
		
		create_effects(item, item['pos'], item['realpos'][2], _z_min)
	
	for pos in _line:
		item['realpos'][2] += item['velocity'][2]
		item['velocity'][2] -= item['velocity'][2]*item['gravity']
		
		if 'drag' in item:
			_drag = item['drag']
		else:
			_drag = item['gravity']
			logging.warning('Improper use of gravity.')
			
		_min_x_vel, _min_y_vel, _max_x_vel, _max_y_vel = get_min_max_velocity(item)
		
		if 0<item['velocity'][0]<0.1 or -.1<item['velocity'][0]<0:
			item['velocity'][0] = 0
		
		if 0<item['velocity'][1]<0.1 or -.1<item['velocity'][1]<0:
			item['velocity'][1] = 0
		
		item['velocity'][0] -= numbers.clip(item['velocity'][0]*_drag, _min_x_vel, _max_x_vel)
		item['velocity'][1] -= numbers.clip(item['velocity'][1]*_drag, _min_y_vel, _max_y_vel)
		
		if 0>pos[0] or pos[0]>=MAP_SIZE[0] or 0>pos[1] or pos[1]>=MAP_SIZE[1]:
			logging.warning('Item OOM: %s', item['uid'])
			delete_item(ITEMS[item_uid])
			return False
		
		if item['type'] == 'bullet':
			for _life in [LIFE[i] for i in LIFE]:
				if _life['id'] == item['owner'] or _life['dead']:
					continue					
				
				if _life['pos'][0] == pos[0] and _life['pos'][1] == pos[1] and _life['pos'][2] == int(round(item['realpos'][2])):
					remove_from_chunk(item)
					item['pos'] = [pos[0],pos[1],_life['pos'][2]]
					add_to_chunk(item)
					life.damage_from_item(_life,item,60)
					delete_item(ITEMS[item_uid])
					return False
			
		if _break:
			break
		
		#_z_max = numbers.clip(int(round(item['realpos'][2]))+1, 0, maputils.get_map_size(WORLD_INFO['map'])[2]-1)
		#if MAP[pos[0]][pos[1]][_z_max]:
		#	item['velocity'][0] = 0
		#	item['velocity'][1] = 0
		#	item['velocity'][2] = 0
		#	item['pos'] = [pos[0],pos[1],item['pos'][2]-1]
		#
		#	print 'LANDED',item['pos']	
		#	_break = True
		#	break
	
		_z_min = numbers.clip(int(round(item['realpos'][2])), 0, maputils.get_map_size(WORLD_INFO['map'])[2]-1)
		if collision_with_solid(item, [pos[0], pos[1], _z_min]):
			_break = True
			break
		
		create_effects(item, pos, item['realpos'][2], _z_min)
	
	remove_from_chunk(item)
	
	if _break:
		item['pos'][0] = int(pos[0])
		item['pos'][1] = int(pos[1])
		item['pos'][2] = int(round(item['realpos'][2]))
	else:
		item['pos'][0] = int(round(item['realpos'][0]))
		item['pos'][1] = int(round(item['realpos'][1]))
		item['pos'][2] = int(round(item['realpos'][2]))
	
	add_to_chunk(item)
	
	_x = item['pos'][0]-CAMERA_POS[0]
	_y = item['pos'][1]-CAMERA_POS[1]
	if 0<=_x<MAP_WINDOW_SIZE[0] and 0<=_y<MAP_WINDOW_SIZE[1]:
		gfx.refresh_window_position(_x, _y)

	if item['pos'][0] < 0 or item['pos'][0] > MAP_SIZE[0] \
          or item['pos'][1] < 0 or item['pos'][1] > MAP_SIZE[1]:
		delete_item(ITEMS[item_uid])
		return False
			
	#elif _break:
	#	maps.refresh_chunk(life.get_current_chunk_id(item))

	_min_x_vel, _min_y_vel, _max_x_vel, _max_y_vel = get_min_max_velocity(item)
	
	if 0<item['velocity'][0]<0.1 or -.1<item['velocity'][0]<0:
		item['velocity'][0] = 0
	
	if 0<item['velocity'][1]<0.1 or -.1<item['velocity'][1]<0:
		item['velocity'][1] = 0
	
	#TODO: This isn't gravity...
	if 'drag' in item:
		_drag = item['drag']
	else:
		_drag = item['gravity']
		logging.warning('Improper use of gravity.')
	
	item['velocity'][0] -= numbers.clip(item['velocity'][0]*_drag, _min_x_vel, _max_x_vel)
	item['velocity'][1] -= numbers.clip(item['velocity'][1]*_drag, _min_y_vel, _max_y_vel)

def tick_all_items(MAP):
	for item in ITEMS.keys():
		tick_item(item)