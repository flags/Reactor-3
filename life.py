from globals import *
import graphics as gfx
import pathfinding
import logging
import numbers
import items
import menus
import copy
import time
import json
import os

def load_life(life):
	with open(os.path.join(LIFE_DIR,life+'.json'),'r') as e:
		return json.loads(''.join(e.readlines()))

def calculate_base_stats(life):
	"""Calculates and returns intital stats for `life`."""
	stats = {'arms': None,
		'legs': None,
		'melee': None,
		'speed_max': LIFE_MAX_SPEED}
	race_type = None
	
	_flags = life['flags'].split('|')
	
	for flag in _flags:
		if _flags.index(flag) == 0:
			race_type = flag
		
		elif flag.count('LEGS'):
			stats['legs'] = flag.partition('[')[2].partition(']')[0].split(',')
		
		elif flag.count('ARMS'):
			stats['arms'] = flag.partition('[')[2].partition(']')[0].split(',')
		
		elif flag.count('HANDS'):
			stats['hands'] = flag.partition('[')[2].partition(']')[0].split(',')
		
		elif flag.count('MELEE'):
			stats['melee'] = flag.partition('[')[2].partition(']')[0].split(',')
	
	stats['base_speed'] = LIFE_MAX_SPEED-(len(stats['legs']))
	stats['speed_max'] = stats['base_speed']
	
	return stats

def get_max_speed(life):
	"""Returns max speed based on items worn."""
	_speed_mod = 0
	
	for limb in get_all_limbs(life['body']):
		for item in life['body'][limb]['holding']:
			_i = get_inventory_item(life,item)
			
			if _i.has_key('speed_mod'):
				_speed_mod += _i['speed_mod']
	
	return LIFE_MAX_SPEED-_speed_mod

def initiate_life(name):
	"""Loads (and returns) new life type into memory."""
	if name in LIFE_TYPES:
		logging.warning('Life type \'%s\' is already loaded. Reloading...' % name)
	
	life = load_life(name)
	
	if not 'icon' in life:
		logging.warning('No icon set for life type \'%s\'. Using default (%s).' % (name,DEFAULT_LIFE_ICON))
		_life['tile'] = DEFAULT_LIFE_ICON
	
	if not 'flags' in life:
		logging.error('No flags set for life type \'%s\'. Errors may occur.' % name)
	
	for key in life:
		if isinstance(life[key],unicode):
			life[key] = str(life[key])
	
	life.update(calculate_base_stats(life))
	
	LIFE_TYPES[name] = life
	
	return life

def initiate_limbs(body):
	"""Creates skeleton of a character and all related variables. Returns nothing."""
	for limb in body:
		#Unicode fix:
		_val = body[limb].copy()
		del body[limb]
		body[str(limb)] = _val
		body[limb] = body[str(limb)]
		
		_flags = body[limb]['flags'].split('|')
		
		if 'CANSTORE' in _flags:
			body[limb]['storing'] = []
		
		body[limb]['holding'] = []
		body[limb]['condition'] = 100
		body[limb]['cut'] = False

def get_limb(body,limb):
	"""Helper function. Finds ands returns a limb."""
	return body[limb]

def get_all_limbs(body):
	"""Deprecated helper function. Returns all limbs."""
	#logging.warning('Deprecated: life.get_all_limbs() will be removed in next version.')
	
	return body

def create_life(type,position=(0,0,2),name=('Test','McChuckski'),map=None):
	"""Initiates and returns a deepcopy of a life type."""
	if not type in LIFE_TYPES:
		raise Exception('Life type \'%s\' does not exist.' % type)
	
	#TODO: Any way to get rid of this call to `copy`?
	_life = copy.deepcopy(LIFE_TYPES[type])
	_life['name'] = name
	_life['speed'] = _life['speed_max']
	_life['pos'] = list(position)
	_life['realpos'] = list(position)
	
	#TODO: We only need this for pathing, so maybe we should move this to
	#the `walk` function?
	_life['map'] = map
	
	_life['path'] = []
	_life['actions'] = []
	_life['item_index'] = 0
	_life['inventory'] = {}
	_life['flags'] = {}
	_life['gravity'] = 0
	_life['targetting'] = None
	
	initiate_limbs(_life['body'])
	LIFE.append(_life)
	
	return _life

def path_dest(life):
	"""Returns the end of the current path."""
	if not life['path']:
		return None
	
	return tuple(life['path'][len(life['path'])-1])

def walk(life,to):
	"""Performs a single walk tick. Waits or returns success of life.walk_path()."""
	if life['speed']:
		life['speed'] -= 1
		return False
	elif life['speed']<=0:
		life['speed'] = life['speed_max']
	
	_dest = path_dest(life)
	
	if not _dest == tuple(to):
		#_stime = time.time()
		_path = pathfinding.astar(start=life['pos'],end=to,size=MAP_SIZE,omap=life['map'])
		life['path'] = _path.find_path(life['pos'])
		#print time.time()-_stime
	
	return walk_path(life)

def walk_path(life):
	"""Walks and returns whether the path is finished or not."""
	if life['gravity']:
		return False
	
	if life['path']:
		_pos = list(life['path'].pop(0))
		
		if _pos[2] and abs(_pos[2])-1:
			if _pos[2]>0:
				logging.debug('%s is changing z-level: %s -> %s' % (life['name'][0],life['pos'][2],life['pos'][2]+(_pos[2]-1)))
				life['pos'][2] += _pos[2]-1
			
		life['pos'] = [_pos[0],_pos[1],life['pos'][2]]
		life['realpos'] = life['pos'][:]
		
		if life['path']:
			return False
		else:
			return True
	else:
		print 'here?'
		return False

def perform_collisions(life):
	"""Performs gravity. Returns True if falling."""
	if not life['map'][life['pos'][0]][life['pos'][1]][life['pos'][2]]:
		if life['map'][life['pos'][0]][life['pos'][1]][life['pos'][2]-1]:
			life['pos'][2] -= 1
			
			return True
		
		if not life['gravity'] and life.has_key('player'):
			gfx.message('You begin to fall...')
		
		life['gravity'] = SETTINGS['world gravity']
			
	elif life['gravity']:
		life['gravity'] = 0
		
		if life.has_key('player'):
			gfx.message('You land.')
	
	if life['gravity']:
		life['realpos'][2] -= SETTINGS['world gravity']
		life['pos'][2] = int(life['realpos'][2])
	
	return False

def get_highest_action(life):
	"""Returns highest action in the queue."""
	_actions = {'action': None,'lowest': -1}
	
	for action in life['actions']:
		if action['score'] > _actions['lowest']:
			_actions['lowest'] = action['score']
			_actions['action'] = action
	
	if _actions['action']:
		return _actions['action']
	else:
		return None

def clear_actions(life):
	"""Clears all actions and prints a cancellation message for the highest scoring action."""
	#TODO: Any way to improve this?
	if life['actions'] and not life['actions'][0]['action']['action']=='move':
		_action = life['actions'][0]['action']['action']
		
		logging.debug('%s %s cancels %s' % (life['name'][0],life['name'][1],_action))
		
		if life.has_key('player'):
			try:
				gfx.message(MESSAGE_BANK['cancel'+_action])
			except KeyError:
				logging.warning('Unhandled cancel message for action \'%s\'.' % _action)
		
	life['actions'] = []

def delete_action(life,action):
	"""Deletes an action."""
	_action = {'action': action['action'],
		'score': action['score'],
		'delay': action['delay']}
	
	life['actions'].remove(_action)

def add_action(life,action,score,delay=0):
	"""Creates new action. Returns True on success."""
	_tmp_action = {'action': action,'score': score}
	
	if not _tmp_action in life['actions']:
		_tmp_action['delay'] = delay
		
		life['actions'].append(_tmp_action)
		
		return True
	
	return False

def perform_action(life):
	"""Executes logic based on top action. Returns True on success."""
	action = get_highest_action(life)
	
	if not action:
		return False
	
	_action = action.copy()
	
	#TODO: What's happening here?
	if not _action in life['actions']:
		return False

	if action['delay']:
		action['delay']-=1
		
		return False

	_score = _action['score']
	_delay = _action['delay']
	_action = _action['action']
	
	if _action['action'] == 'move':
		if tuple(_action['to']) == tuple(life['pos']) or walk(life,_action['to']):
			delete_action(life,action)
	
	elif _action['action'] == 'pickupitem':
		direct_add_item_to_inventory(life,_action['item'],container=_action['container'])
		delete_action(life,action)
		
		if life.has_key('player'):			
			if _action.has_key('container'):
				gfx.message('You store %s in your %s.'
					% (items.get_name(_action['item']),_action['container']['name']))
	
	elif _action['action'] == 'dropitem':
		_name = items.get_name(get_inventory_item(life,_action['item']))
		
		if item_is_equipped(life,_action['item']):
			gfx.message('You take off %s.' % _name)
				
		_stored = item_is_stored(life,_action['item'])
		if _stored:
			_item = get_inventory_item(life,_action['item'])
			gfx.message('You remove %s from your %s.' % (_name,_stored['name']))
		
		gfx.message('You drop %s.' % _name)
		drop_item(life,_action['item'])
		
		delete_action(life,action)
	
	elif _action['action'] == 'equipitem':
		_name = items.get_name(get_inventory_item(life,_action['item']))
		
		if not equip_item(life,_action['item']):
			delete_action(life,action)
			gfx.message('You can\'t wear %s.' % _name)
		
		_stored = item_is_stored(life,_action['item'])

		if _stored:
			gfx.message('You remove %s from your %s.' % (_name,_stored['name']))
		
		delete_action(life,action)
		
		gfx.message('You put on %s.' % _name)

	elif _action['action'] == 'pickupequipitem':
		if not can_wear_item(life,_action['item']):
			if life.has_key('player'):
				gfx.message('You can\'t equip this item!')
			
			delete_action(life,action)
			
			return False
		
		#TODO: Can we even equip this? Can we check here instead of later?
		_id = direct_add_item_to_inventory(life,_action['item'])
		
		equip_item(life,_id)
		
		delete_action(life,action)
		
		if life.has_key('player'):
			gfx.message('You equip %s from the ground.' % items.get_name(_action['item']))
	
	elif _action['action'] == 'pickupholditem':
		_hand = get_limb(life['body'],_action['hand'])
		
		if _hand['holding']:
			if life.has_key('player'):
				gfx.message('You\'re alreading holding something in your %s!' % _action['hand'])
		
			delete_action(life,action)
			
			return False
		
		_id = direct_add_item_to_inventory(life,_action['item'])
		_hand['holding'].append(_id)
		
		if 'player' in life:
			gfx.message('You hold %s in your %s.' % (items.get_name(_action['item']),_action['hand']))
		
		delete_action(life,action)
	
	elif _action['action'] == 'removeandholditem':
		_hand = can_hold_item(life)
		
		if not _hand:
			if 'player' in life:
				_item = get_inventory_item(life,_action['item'])
				gfx.message('You have no hands free to hold the %s.' % items.get_name(_item))
			
			return False

		#TODO: Do we need to drop it first?
		_dropped_item = remove_item_from_inventory(life,_action['item'])
		_id = direct_add_item_to_inventory(life,_dropped_item)
		_hand['holding'].append(_id)
		
		if 'player' in life:
			gfx.message('You hold %s.' % items.get_name(_dropped_item))
		
		delete_action(life,action)
	
	elif _action['action'] == 'holditemthrow':
		_dropped_item = drop_item(life,_action['item'])
		_id = direct_add_item_to_inventory(life,_dropped_item)
		_action['hand']['holding'].append(_id)
		
		gfx.message('You aim %s.' % items.get_name(_dropped_item))
		life['targetting'] = life['pos'][:]
		
		delete_action(life,action)
		
	elif _action['action'] == 'reload':	
		_action['weapon'][_action['weapon']['feed']] = _action['ammo']
		_ammo = remove_item_from_inventory(life,_action['ammo']['id'])
		_action['ammo']['parent'] = _action['weapon']
		
		if life.has_key('player'):
			gfx.message('You load a new %s into your %s.' % (_action['weapon']['feed'],_action['weapon']['name']))
		
		delete_action(life,action)
	
	elif _action['action'] == 'unload':	
		_ammo = _action['weapon'][_action['weapon']['feed']]
		_hand = can_hold_item(life)
		
		if _hand:
			_id = direct_add_item_to_inventory(life,_ammo)
			del _ammo['parent']
			_hand['holding'].append(_id)
			_action['weapon'][_action['weapon']['feed']] = None
		else:
			if 'player' in life:
				gfx.message('You have no hands free to hold %s!' % items.get_name(_ammo))
				gfx.message('%s falls to the ground.' % items.get_name(_ammo))
			
			#TODO: Too hacky
			del _ammo['parent']
			_ammo['pos'] = life['pos'][:]
		
		delete_action(life,action)
	
	elif _action['action'] == 'refillammo':	
		_action['ammo']['rounds'].append(_action['round'])
		_round = remove_item_from_inventory(life,_action['round']['id'])
		
		if life.has_key('player') and len(_action['ammo']['rounds'])>=_action['ammo']['maxrounds']:
			gfx.message('The magazine is full.')
		
		delete_action(life,action)
	
	return True

def tick(life):
	"""Wrapper function. Performs all life-related logic. Returns nothing."""
	perform_collisions(life)
	perform_action(life)

def attach_item_to_limb(body,id,limb):
	"""Attaches item to limb. Returns True."""
	body[limb]['holding'].append(id)
	logging.debug('%s attached to %s' % (id,limb))
	
	return True

def remove_item_from_limb(body,item,limb):
	"""Removes item from limb. Returns True."""
	body[limb]['holding'].remove(item)
	logging.debug('%s removed from %s' % (item,limb))
	
	return True

def get_all_storage(life):
	"""Returns list of all containers in a character's inventory."""
	return [item for item in [life['inventory'][item] for item in life['inventory']] if 'max_capacity' in item]

def can_throw(life):
	"""Helper function for use where life.can_hold_item() is out of place. See referenced function."""
	return can_hold_item(life)

def throw_item(life,id,target,speed):
	"""Removes item from inventory and sets its movement towards a target. Returns nothing."""
	_item = remove_item_from_inventory(life,id)
	
	direction = numbers.direction_to(life['pos'],target)
	
	items.move(_item,direction,speed)

def update_container_capacity(life,container):
	"""Updates the current capacity of container. Returns nothing."""
	logging.warning('life.update_container_capacity(): This method is untested!')
	_capacity = 0
	
	for item in container['storing']:
		_capacity += get_inventory_item(life,item)['size']
	
	container['capacity'] = _capacity

def can_put_item_in_storage(life,item):
	"""Returns available storage container that can fit `item`. Returns False if none is found."""
	#TODO: Should return list of containers instead.
	#Whoa...
	for _item in [life['inventory'][_item] for _item in life['inventory']]:
		if 'max_capacity' in _item and _item['capacity']+item['size'] < _item['max_capacity']:
			return _item
		else:
			pass
	
	return False

def add_item_to_storage(life,item,container=None):
	"""Adds item to free storage container.
	
	A specific container can be requested with the keyword argument `container`.
	
	"""
	if not container:
		container = can_put_item_in_storage(life,item)
	
	if not container:
		return False
	
	container['storing'].append(item['id'])
	container['capacity'] += item['size']
	
	return True

def remove_item_in_storage(life,id):
	"""Removes item from strorage. Returns storage container on success. Returns False on failure."""
	for _container in [life['inventory'][_container] for _container in life['inventory']]:
		if not 'max_capacity' in _container:
			continue

		if id in _container['storing']:
			_container['storing'].remove(id)
			_container['capacity'] -= get_inventory_item(life,id)['size']
			logging.debug('Removed item #%s from %s' % (id,_container['name']))
			
			return _container
	
	return False

def item_is_stored(life,id):
	"""Returns the container of an item. Returns False on failure."""
	for _container in [life['inventory'][_container] for _container in life['inventory']]:
		if not 'max_capacity' in _container:
			continue

		if id in _container['storing']:
			return _container
	
	return False

def can_wear_item(life,item):
	"""Attaches item to limbs. Returns False on failure."""
	#TODO: Function name makes no sense.	
	for limb in item['attaches_to']:
		_limb = get_limb(life['body'],limb)
		
		for _item in [life['inventory'][str(i)] for i in _limb['holding']]:
			if not 'CANSTACK' in _item['flags']:
				logging.warning('%s will not let %s stack.' % (_item['name'],item['name']))
				return False

	return True

def get_inventory_item(life,id):
	"""Returns inventory item."""
	if not life['inventory'].has_key(str(id)):
		raise Exception('Life \'%s\' does not have item of id #%s'
			% (life['name'][0],id))
	
	return life['inventory'][str(id)]

def get_all_inventory_items(life,matches=None):
	"""Returns list of all inventory items.
	
	`matches` can be a list of dictionaries with criteria the item must meet. Only one needs to match.
	
	"""
	_items = []
	
	for item in life['inventory']:
		_item = life['inventory'][item]
		
		if matches:
			if not perform_match(_item,matches):
				continue
		
		_items.append(_item)
		
	return _items

def direct_add_item_to_inventory(life,item,container=None):
	"""Dangerous function. Adds item to inventory, bypassing all limitations normally applied. Returns inventory ID.
	
	A specific container can be requested with the keyword argument `container`.
	
	""" 
	#Warning: Only use this if you know what you're doing!
	life['item_index'] += 1
	_id = life['item_index']
	item['id'] = _id
	
	life['inventory'][str(_id)] = item
	
	if 'max_capacity' in item:
		logging.debug('Container found in direct_add')
		
		for uid in item['storing'][:]:
			logging.debug('\tAdding uid %s' % uid)
			_item = items.get_item_from_uid(uid)

			item['storing'].remove(uid)
			item['storing'].append(direct_add_item_to_inventory(life,_item))
	
	#Warning: `container` refers directly to an item instead of an ID.
	if container:
		#Warning: No check is done to make sure the container isn't full!
		add_item_to_storage(life,item,container=container)
	
	return _id

def add_item_to_inventory(life,item):
	"""Helper function. Adds item to inventory. Returns inventory ID."""
	life['item_index'] += 1
	_id = life['item_index']
	item['id'] = _id
	
	if not add_item_to_storage(life,item):
		if not can_wear_item(life,item):
			life['item_index'] -= 1
			del item['id']
			
			return False
		else:
			life['inventory'][str(_id)] = item
			equip_item(life,_id)
	else:
		life['inventory'][str(_id)] = item
	
	if 'max_capacity' in item:
		for uid in item['storing'][:]:
			_item = items.get_item_from_uid(uid)
			
			item['storing'].remove(uid)
			item['storing'].append(direct_add_item_to_inventory(life,_item))
	
	logging.debug('%s got \'%s\'.' % (life['name'][0],item['name']))
	
	return _id

def remove_item_from_inventory(life,id):
	"""Removes item from inventory and all storage containers. Returns item."""
	item = get_inventory_item(life,id)
	
	_holding = is_holding(life,id)
	if _holding:
		_holding['holding'].remove(id)
		logging.debug('%s stops holding a %s' % (life['name'][0],item['name']))
		
	elif item_is_equipped(life,id):
		logging.debug('%s takes off a %s' % (life['name'][0],item['name']))
	
		for limb in item['attaches_to']:
			remove_item_from_limb(life['body'],item['id'],limb)
		
		item['pos'] = life['pos'][:]
	elif item_is_stored(life,id):
		remove_item_in_storage(life,id)
	
	if 'max_capacity' in item:
		logging.debug('Dropping container storing:')
		
		for _item in item['storing'][:]:
			logging.debug('\tdropping %s' % _item)
			item['storing'].remove(_item)
			item['storing'].append(get_inventory_item(life,_item)['uid'])
			
			del life['inventory'][str(_item)]
	
	life['speed_max'] = get_max_speed(life)
	
	logging.debug('Removed from inventory: %s' % item['name'])
	
	del life['inventory'][str(item['id'])]
	del item['id']
	
	return item

def _equip_clothing(life,id):
	"""Private function. Equips clothing. See life.equip_item()."""
	item = get_inventory_item(life,id)
	
	if not can_wear_item(life,item):
		return False
	
	_limbs = get_all_limbs(life['body'])
	
	#TODO: Faster way to do this with sets
	for limb in item['attaches_to']:
		if not limb in _limbs:
			logging.warning('Limb not found: %s' % limb)
			return False
	
	remove_item_in_storage(life,id)
	
	logging.debug('%s puts on a %s.' % (life['name'][0],item['name']))
	
	if item['attaches_to']:			
		for limb in item['attaches_to']:
			attach_item_to_limb(life['body'],item['id'],limb)
	
	return True

def _equip_weapon(life,id):
	"""Private function. Equips weapon. See life.equip_item()."""
	_limbs = get_all_limbs(life['body'])
	_hand = can_hold_item(life)
	item = get_inventory_item(life,id)
	
	if not _hand:
		if 'player' in life:
			gfx.message('You don\'t have a free hand!')
		return False
	
	remove_item_in_storage(life,id)
	_hand['holding'].append(id)
	
	logging.debug('%s equips a %s.' % (life['name'][0],item['name']))
	
	return True

def equip_item(life,id):
	"""Helper function. Equips item."""	
	item = get_inventory_item(life,id)
	
	if item['type'] == 'clothing':
		if not _equip_clothing(life,id):
			return False
	elif item['type'] == 'gun':
		_equip_weapon(life,id)
	else:
		logging.error('Invalid item type: %s' % item['type'])
	
	life['speed_max'] = get_max_speed(life)
	
	if life['speed'] > life['speed_max']:
		life['speed'] = life['speed_max']
	
	return True

def drop_item(life,id):
	"""Helper function. Removes item from inventory and drops it. Returns item."""
	item = remove_item_from_inventory(life,id)
	item['pos'] = life['pos'][:]
	
	return item

def pick_up_item_from_ground(life,uid):
	"""Helper function. Adds item via UID. Returns inventory ID. Raises exception otherwise."""
	#TODO: Misleading function name.
	_item = items.get_item_from_uid(uid)
	_id = add_item_to_inventory(life,_item)
	
	if _id:
		return _id

	raise Exception('Item \'%s\' does not exist at (%s,%s,%s).'
		% (item,life['pos'][0],life['pos'][1],life['pos'][2]))

def can_hold_item(life):
	"""Returns limb of empty hand. Returns False if none are empty."""
	for hand in life['hands']:
		_hand = get_limb(life['body'],hand)
		
		if not _hand['holding']:
			return _hand
	
	return False

def is_holding(life,id):
	"""Returns the hand holding `item`. Returns False otherwise."""
	for hand in life['hands']:
		_limb = get_limb(life['body'],hand)
		
		if id in _limb['holding']:
			return _limb
	
	return False

def perform_match(item,matches):
	for match in matches:
		_fail = False
		
		for key in match:
			if not key in item:
				_fail = True
				break
			
			if not match[key] == item[key]:
				_fail = True
				break
		
		if not _fail:
			return True
	
	return False

def get_held_items(life,matches=None):
	"""Returns list of all held items."""
	_holding = []
	
	for hand in life['hands']:
		_limb = get_limb(life['body'],hand)
		
		if _limb['holding']:
			_item = get_inventory_item(life,_limb['holding'][0])
			
			if matches:
				if not perform_match(_item,matches):
					continue
							
			_holding.append(_limb['holding'][0])
	
	return _holding

def item_is_equipped(life,id,check_hands=False):
	"""Returns limb where item is equipped. Returns False othewise.
	
	The `check_hands` keyword argument indicates whether hands will be checked (default False)
	
	"""
	for _limb in get_all_limbs(life['body']):
		if not check_hands and _limb in life['hands']:
			continue
		
		if int(id) in get_limb(life['body'],_limb)['holding']:
			return True
	
	return False

def show_life_info(life):
	for key in life:
		if key == 'body':
			continue
		
		logging.debug('%s: %s' % (key,life[key]))
	
	return True

def draw_life():
	for life in LIFE:		
		if life['pos'][0] >= CAMERA_POS[0] and life['pos'][0] < CAMERA_POS[0]+MAP_WINDOW_SIZE[0] and\
			life['pos'][1] >= CAMERA_POS[1] and life['pos'][1] < CAMERA_POS[1]+MAP_WINDOW_SIZE[1]:
			_x = life['pos'][0] - CAMERA_POS[0]
			_y = life['pos'][1] - CAMERA_POS[1]
			
			if not LOS_BUFFER[0][_y,_x]:
				continue
			
			gfx.blit_char(_x,
				_y,
				life['icon'],
				white,
				None,
				char_buffer=MAP_CHAR_BUFFER,
				rgb_fore_buffer=MAP_RGB_FORE_BUFFER,
				rgb_back_buffer=MAP_RGB_BACK_BUFFER)

def get_fancy_inventory_menu_items(life,show_equipped=True,check_hands=False,matches=None):
	"""Returns list of menu items with "fancy formatting".
	
	`show_equipped` decides whether equipped items are shown (default True)
	`check_hands` decides whether held items are shown (default False)
	
	"""
	_inventory = []
		
	#TODO: Time it would take to remove
	if show_equipped:
		_title = menus.create_item('title','Equipped',None,enabled=False)
		_inventory.append(_title)
	
		for entry in life['inventory']:
			item = get_inventory_item(life,entry)
			
			if matches:
				if not perform_match(item,matches):
					continue					
			
			if item_is_equipped(life,entry,check_hands=check_hands):
				_menu_item = menus.create_item('single',
					item['name'],
					'Equipped',
					icon=item['icon'],
					id=int(entry))
			
				_inventory.append(_menu_item)
	elif check_hands:
		_title = menus.create_item('title','Holding',None,enabled=False)
		_inventory.append(_title)
	
		for hand in life['hands']:
			if not life['body'][hand]['holding']:
				continue
				
			item = get_inventory_item(life,life['body'][hand]['holding'][0])
			
			if matches:
				if not perform_match(item,matches):
					continue	
			
			_menu_item = menus.create_item('single',
				item['name'],
				'Holding',
				icon=item['icon'],
				id=item['id'])
		
			_inventory.append(_menu_item)
	
	for container in get_all_storage(life):
		_title = menus.create_item('title',
			'%s - %s/%s' % (container['name'],container['capacity'],container['max_capacity']),
			None,
			enabled=False)
		
		_inventory.append(_title)
		for _item in container['storing']:
			item = get_inventory_item(life,_item)
			
			if matches:
				if not perform_match(item,matches):
					continue	
			
			_menu_item = menus.create_item('single',
				item['name'],
				'Not equipped',
				icon=item['icon'],
				id=int(_item))
			
			_inventory.append(_menu_item)
	
	return _inventory

def draw_visual_inventory(life):
	_inventory = {}
	_limbs = get_all_limbs(life['body'])
	
	for limb in _limbs:
		if _limbs[limb]['holding']:
			_item = get_inventory_item(life,_limbs[limb]['holding'][0])
			console_set_default_foreground(0,white)
			console_print(0,MAP_WINDOW_SIZE[0]+1,_limbs.keys().index(limb)+1,'%s: %s' % (limb,_item['name']))
		else:
			console_set_default_foreground(0,Color(125,125,125))
			console_print(0,MAP_WINDOW_SIZE[0]+1,_limbs.keys().index(limb)+1,'%s: None' % limb)
	
	console_set_default_foreground(0,white)

def cut_limb(life,limb):
	_limb = life['body'][limb]
	
	if _limb['cut']:
		return True
	
	_limb['cut'] = True
	
	if life.has_key('player'):
		gfx.message('Your %s is severely cut!' % limb)

def damage(life,item):
	if item['sharp']:
		cut_limb(life,'chest')
	
	_damage = item['damage']#-armor here
	_damage -= abs(item['maxvelocity'][0]-item['velocity'][0])+abs(item['maxvelocity'][1]-item['velocity'][1])
	
	life['body']['chest']['condition'] -= _damage
	
	if life.has_key('player'):
		gfx.message('You feel a sudden force against you. (-%s)' % _damage)

def tick_all_life():
	for life in LIFE:
		tick(life)
