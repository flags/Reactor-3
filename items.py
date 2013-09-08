from globals import *

import graphics as gfx

import scripting
import maputils
import drawing
import numbers
import effects
import timers
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
				logging.error('Bspecies mismatch in item \'%s\': Expected \']\'' % name)
				continue
			elif _ocount < _ccount:
				logging.error('Bspecies mismatch in item \'%s\': Expected \'[\'' % name)
				continue
			
			_flags[flag.split('[')[0]] = scripting.initiate(item, flag)
		else:
			_flags[flag] = None
	
	item['flags'] = _flags
	item['size'] = 	[int(c) for c in item['size'].split('x')]
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
	
	if 'speed' in item:
		item['max_speed'] = item['speed']
	else:
		item['max_speed'] = 2
	
	ITEMS[item['uid']] = item
	
	WORLD_INFO['itemid'] += 1
	return item['uid']

def delete_item(item):
	logging.debug('Deleting references to item %s' % item['uid'])
	
	for life in [LIFE[i] for i in LIFE]:
		if item['uid'] in life['know_items']:
			logging.debug('\tDeleted reference in life #%s' % life['id'])
			
			del life['know_items'][item['uid']]
	
	timers.remove_by_owner(item)
	
	if gfx.position_is_in_frame(item['pos']):
		gfx.refresh_window_position(item['pos'][0]-CAMERA_POS[0], item['pos'][1]-CAMERA_POS[1])
	
	del ITEMS[item['uid']]

def save_all_items():
	for item in ITEMS.values():
		item['icon'] = ord(item['icon'])

def reload_all_items():
	for item in ITEMS.values():
		item['icon'] = chr(item['icon'])

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
		
		if item.has_key('parent_id'):
			continue
		
		if item.has_key('parent'):
			continue
		
		if item['pos'] == position:
			_items.append(item)
	
	return _items

def get_name(item):
	"""Returns the full name of an item."""
	return '%s %s' % (item['prefix'],item['name'])		

def move(item, direction, speed, friction=0.05, _velocity=0):
	"""Sets new velocity for an item. Returns nothing."""
	velocity = numbers.velocity(direction, speed)
	velocity[2] = _velocity
	
	item['friction'] = friction
	item['velocity'] = velocity
	item['realpos'] = item['pos'][:]
	
	logging.debug('%s flies off in an arc! (%s)' % (get_name(item), item['velocity']))

def draw_items():
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if item.has_key('parent_id'):
			continue
		
		if item.has_key('parent'):
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
				tcod.white,
				None,
				char_buffer=MAP_CHAR_BUFFER,
				rgb_fore_buffer=MAP_RGB_FORE_BUFFER,
				rgb_back_buffer=MAP_RGB_BACK_BUFFER)

def can_store_item_in(item_uid, container_uid):
	_item = get_item_from_uid(item_uid)
	_container = get_item_from_uid(container_uid)
	
	if 'max_capacity' in _container and _container['capacity']+_item['size'] < _container['max_capacity']:
		return container_uid
		
	return False

def storage_item_in(life, item_uid, container_uid):
	if not can_store_item_in(item_uid, container_uid):
		return False
	
	_item = get_item_from_uid(item_uid)
	
	_container = items.get_item_from_uid(container_uid)
	_container['storing'].append(item_uid)
	_container['capacity'] += _item['size']
	
	update_container_capacity(life, _container)
	
	return True

def explode(item):
	if not item['type'] == 'explosive':
		return False
	
	effects.create_light(item['pos'], (255, 255, 255), item['damage']['force']*2, 0, fade=0.8)
	
	if 'fire' in item['damage']:
		for pos in drawing.draw_circle(item['pos'], item['radius']):
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
	elif not pos[0]+1 <= MAP_SIZE[0]-1 and item['velocity'][0]>0 and WORLD_INFO['map'][pos[0]+1][pos[1]][pos[2]+_z]:
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
					item['pos'] = [pos[0],pos[1],_life['pos'][2]]
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
	
	if _break:
		item['pos'][0] = int(pos[0])
		item['pos'][1] = int(pos[1])
		item['pos'][2] = int(round(item['realpos'][2]))
	else:
		item['pos'][0] = int(round(item['realpos'][0]))
		item['pos'][1] = int(round(item['realpos'][1]))
		item['pos'][2] = int(round(item['realpos'][2]))
	
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