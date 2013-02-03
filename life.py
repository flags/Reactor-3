from globals import *
import graphics as gfx
import pathfinding
import language
import drawing
import logging
import weapons
import numbers
import effects
import random
import alife
import items
import menus
import copy
import time
import json
import os

try:
	import render_los
	CYTHON_RENDER_LOS = True
except:
	CYTHON_RENDER_LOS = False

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

def calculate_limb_conditions(life):
	for limb in [life['body'][limb] for limb in life['body']]:
		_pain_mod = numbers.clip(limb['pain'],1,100)
		_condition = 100
		
		if limb['bleeding']:
			_condition-=(3*_pain_mod)
		
		if limb['cut']:
			_condition-=(5*_pain_mod)
		
		if limb['bruised']:
			_condition-=(1*_pain_mod)
		
		if limb['broken']:
			_condition-=(7*_pain_mod)
		
		limb['condition'] = _condition

def get_limb_condition(life,limb):
	return life['body'][limb]['condition']

def get_max_speed(life):
	"""Returns max speed based on items worn."""
	_speed_mod = 0
	_penalty = 0
	
	for limb in life['body']:
		for item in life['body'][limb]['holding']:
			_i = get_inventory_item(life,item)
			
			if _i.has_key('speed_mod'):
				_speed_mod += _i['speed_mod']
		
		if limb in life['legs']:
			_pain = life['body'][limb]['pain']
			
			if not _pain:
				_pain = 1
			
			_penalty += int((100-life['body'][limb]['condition'])*DAMAGE_MOVE_PENALTY_MOD)*_pain
	
	_MAX_SPEED = (LIFE_MAX_SPEED-_speed_mod)+_penalty
	
	if _MAX_SPEED > LIFE_MAX_SPEED:
		return LIFE_MAX_SPEED
	
	return _MAX_SPEED

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
		
		#Note: `Condition` is calculated automatically
		body[limb]['condition'] = 100
		body[limb]['cut'] = False
		body[limb]['bleeding'] = False
		body[limb]['bruised'] = False
		body[limb]['broken'] = False
		body[limb]['pain'] = 0
		
		if not 'parent' in body[limb]:
			continue
		
		if not 'children' in body[body[limb]['parent']]:
			body[body[limb]['parent']]['children'] = [limb]
		else:
			body[body[limb]['parent']]['children'].append(limb)

def get_limb(body,limb):
	"""Helper function. Finds ands returns a limb."""
	return body[limb]

def get_all_limbs(body):
	"""Deprecated helper function. Returns all limbs."""
	#logging.warning('Deprecated: life.get_all_limbs() will be removed in next version.')
	
	return body

def create_and_update_self_snapshot(life):
	_ss = alife.create_snapshot(life)
	alife.update_self_snapshot(life,_ss)
	
	logging.debug('%s updated their snapshot.' % life['name'][0])

def create_life(type,position=(0,0,2),name=('Test','McChuckski'),map=None):
	"""Initiates and returns a deepcopy of a life type."""
	if not type in LIFE_TYPES:
		raise Exception('Life type \'%s\' does not exist.' % type)
	
	#TODO: Any way to get rid of this call to `copy`?
	_life = copy.deepcopy(LIFE_TYPES[type])
	_life['name'] = name
	_life['id'] = SETTINGS['lifeid']
	
	_life['speed'] = _life['speed_max']
	_life['pos'] = list(position)
	_life['realpos'] = list(position)
	
	#TODO: We only need this for pathing, so maybe we should move this to
	#the `walk` function?
	_life['map'] = map
	
	_life['path'] = []
	_life['actions'] = []
	_life['conversations'] = []
	_life['heard'] = []
	_life['item_index'] = 0
	_life['inventory'] = {}
	_life['flags'] = {}
	_life['gravity'] = 0
	_life['targetting'] = None
	_life['pain_tolerance'] = 15
	_life['asleep'] = 0
	_life['blood'] = 300
	_life['consciousness'] = 100
	_life['dead'] = False
	_life['snapshot'] = {}
	_life['in_combat'] = False
	
	#ALife
	_life['know'] = {}
	_life['memory'] = []
	
	initiate_limbs(_life['body'])
	SETTINGS['lifeid'] += 1
	LIFE.append(_life)
	
	return _life

def create_conversation(life,gist,say=None,action=None):
	_convo = {'gist': gist,'say': say,'action': action,'heard': []}
	
	if gist in [convo['gist'] for convo in life['conversations']]:
		return False
	
	logging.debug('Created new conversation: %s' % gist)
	
	for entry in LIFE:
		if entry['id'] == life['id']:
			continue
		
		#TODO: 30?
		if numbers.distance(life['pos'],entry['pos'])<=30:
			hear(entry,{'from': life,'gist': gist})
	
	life['conversations'].append(_convo)
	
	create_and_update_self_snapshot(life)

def hear(life,what):
	what['when'] = time.time()
	life['heard'].append(what)
	
	logging.debug('%s heard %s.' % (' '.join(life['name']),' '.join(what['from']['name'])))

def say(life,text,action=False):
	if action:
		text = text.replace('@n',' '.join(life['name']))
	else:
		text = '%s: %s' % (' '.join(life['name']),text)
	
	print text
	gfx.message(text)

def memory(life,memory,**kvargs):
	_entry = {'text': memory}
	_entry.update(kvargs)
	print _entry
	life['memory'].append(_entry)

def get_recent_memories(life,number):
	return life['memory'][len(life['memory'])-number:]

def create_recent_history(life,depth=10):
	_story = ''
	
	_line = '%s %s ' % (life['name'][0],life['name'][1])
	for entry in life['memory'][len(life['memory'])-depth:]:
		_line += '%s.' % entry['text']
	
	return _line	

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
		life['speed_max'] = get_max_speed(life)
		life['speed'] = life['speed_max']
	
	_dest = path_dest(life)
	
	if not _dest or not (_dest[0],_dest[1]) == tuple(to):
		_stime = time.time()
		life['path'] = pathfinding.create_path(life['pos'],to,source_map=life['map'])
		#print '\ttotal',time.time()-_stime
	
	return walk_path(life)

def walk_path(life):
	"""Walks and returns whether the path is finished or not."""
	if life['gravity']:
		return False
	
	if life['path']:
		_pos = list(life['path'].pop(0))
		
		if _pos[2] and abs(_pos[2])-1:
			if _pos[2]>0:
				#logging.debug('%s is changing z-level: %s -> %s' % (life['name'][0],life['pos'][2],life['pos'][2]+(_pos[2]-1)))
				life['pos'][2] += _pos[2]-1
			
		life['pos'] = [_pos[0],_pos[1],life['pos'][2]]
		life['realpos'] = life['pos'][:]
		
		if life['path']:
			return False
		else:
			return True
	else:
		#TODO: Collision with wall
		return True

def perform_collisions(life):
	"""Performs gravity. Returns True if falling."""
	if not life['map'][life['pos'][0]][life['pos'][1]][life['pos'][2]]:
		if life['map'][life['pos'][0]][life['pos'][1]][life['pos'][2]-1]:
			life['pos'][2] -= 1
			
			return True
		
		if not life['gravity']:
			life['falling_startzpos'] = life['pos'][2]
			
			if life.has_key('player'):
				gfx.message('You begin to fall...')
		
		life['gravity'] = SETTINGS['world gravity']
			
	elif life['gravity']:
		life['gravity'] = 0
		
		_fall_dist = life['falling_startzpos']-life['pos'][2]
		
		if not damage_from_fall(life,_fall_dist) and life.has_key('player'):
			gfx.message('You land.')
	
	if life['gravity']:
		life['realpos'][2] -= SETTINGS['world gravity']
		life['pos'][2] = int(life['realpos'][2])
	
	return False

def get_highest_action(life):
	"""Returns highest action in the queue."""
	#_actions = {'action': None,'lowest': -1}
	
	#for action in life['actions']:
	#	if action['score'] > _actions['lowest']:
	#		_actions['lowest'] = action['score']
	#		_actions['action'] = action
	
	if life['actions'] and life['actions'][0]:
		return life['actions'][0]
	else:
		return None

def clear_actions_matching(life,matches):
	for match in matches[:]:
		for action in life['actions']:
			for key in match:
				if key in action['action'] and match[key] == action['action'][key]:
					life['actions'].remove(action)
					#print 'Removed matched item: ',action
					break

def clear_actions(life,matches=[]):
	"""Clears all actions and prints a cancellation message for the highest scoring action."""
	
	if matches:
		clear_actions_matching(life,matches)
		return True
	else:
		clear_actions_matching(life,matches=[{'action': 'move'}])
		return True

def find_action(life,matches=[{}]):
	_matching_actions = []
	
	for action in [action['action'] for action in life['actions']]:
		_break = False
		
		for match in matches:
			for key in match:
				if not action[key] == match[key]:
					break
					_break = True
			
			if _break:
				break
				
			_matching_actions.append(action)
	
	return _matching_actions

def delete_action(life,action):
	"""Deletes an action."""
	_action = {'action': action['action'],
		'score': action['score'],
		'delay': action['delay']}
	
	life['actions'].remove(_action)

def add_action(life,action,score,delay=0):
	"""Creates new action. Returns True on success."""
	_tmp_action = {'action': action,'score': score}
	
	if _tmp_action in life['actions']:
		return False
	
	_tmp_action['delay'] = delay
	
	if _tmp_action in life['actions']:
		return False
	
	_index = 0
	for queue_action in life['actions']:
		if score > queue_action['score']:
			break
		
		_index += 1
	
	life['actions'].insert(_index,_tmp_action)	
	
	return True

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
			if 'player' in life:
				gfx.message('You take off %s.' % _name)
			else:
				say(life,'@n takes off %s.' % _name,action=True)
				
		_stored = item_is_stored(life,_action['item'])
		if _stored:
			_item = get_inventory_item(life,_action['item'])
			
			if life.has_key('player'):
				gfx.message('You remove %s from your %s.' % (_name,_stored['name']))
			else:
				say(life,'@n takes off %s.' % _name,action=True)
		
		if life.has_key('player'):
			gfx.message('You drop %s.' % _name)
		else:
			say(life,'@n drops %s.' % _name,action=True)
		
		drop_item(life,_action['item'])
		
		delete_action(life,action)
	
	elif _action['action'] == 'equipitem':
		_name = items.get_name(get_inventory_item(life,_action['item']))
		
		if not equip_item(life,_action['item']):
			delete_action(life,action)
			gfx.message('You can\'t wear %s.' % _name)
			
			return False
		
		_stored = item_is_stored(life,_action['item'])

		if _stored:
			if 'player' in life:
				gfx.message('You remove %s from your %s.' % (_name,_stored['name']))
			else:
				pass
		
		delete_action(life,action)
		
		if 'player' in life:
			gfx.message('You put on %s.' % _name)
		else:
			pass

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
				gfx.message('You\'re already holding something in your %s!' % _action['hand'])
		
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
		_action['round']['parent'] = _action['ammo']
		_round = remove_item_from_inventory(life,_action['round']['id'])
		
		if life.has_key('player') and len(_action['ammo']['rounds'])>=_action['ammo']['maxrounds']:
			gfx.message('The magazine is full.')
		
		delete_action(life,action)
	
	elif _action['action'] == 'shoot':
		weapons.fire(life,_action['target'])
		
		delete_action(life,action)
	
	else:
		logging.warning('Unhandled action: %s' % _action['action'])
	
	return True

def kill(life,how):
	if how == 'bleedout':
		if 'player' in life:
			gfx.message('You die from blood loss.',style='death')
		else:
			logging.debug('%s dies from blood loss.' % life['name'][0])
	
	life['dead'] = True

def tick(life,source_map):
	"""Wrapper function. Performs all life-related logic. Returns nothing."""
	if life['dead']:
		return False
	
	#print get_total_pain(life)
	
	if calculate_blood(life)<=0:
		kill(life,'bleedout')
				
		return False
	
	natural_healing(life)
	
	if life['asleep']:
		life['asleep'] -= 1
		
		if life['asleep']<=0:
			life['asleep'] = 0
			
			logging.debug('%s woke up.' % life['name'][0])
			
			if 'player' in life:
				gfx.message('You wake up.')
		
		return False
	
	if get_total_pain(life)>life['pain_tolerance']:		
		life['consciousness'] -= get_total_pain(life)-life['pain_tolerance']
		
		if life['consciousness'] <= 0:
			life['consciousness'] = 0
			
			if 'player' in life:
				gfx.message('The pain becomes too much.')
			else:
				say(life,'@n passes out.',action=True)
			
			pass_out(life)
			
			return False
	
	calculate_limb_conditions(life)
	perform_collisions(life)
	
	if not 'player' in life:
		alife.think(life,source_map)
	
	perform_action(life)

def attach_item_to_limb(body,id,limb):
	"""Attaches item to limb. Returns True."""
	body[limb]['holding'].append(id)
	logging.debug('%s attached to %s' % (id,limb))
	
	return True

def remove_item_from_limb(life,item,limb):
	"""Removes item from limb. Returns True."""
	life['body'][limb]['holding'].remove(item)
	create_and_update_self_snapshot(life)
	logging.debug('%s removed from %s' % (item,limb))
	
	return True

def get_all_storage(life):
	"""Returns list of all containers in a character's inventory."""
	return [item for item in [life['inventory'][item] for item in life['inventory']] if 'max_capacity' in item]

def get_all_visible_items(life):
	return [limb['holding'] for limb in [life['body'][limb] for limb in life['body']] if limb['holding']]

def can_see(life,pos):
	"""Returns `true` if the life can see a certain position."""
	if CYTHON_RENDER_LOS:
		_line = render_los.draw_line(life['pos'][0],
			life['pos'][1],
			pos[0],
			pos[1])
		
		if not _line:
			_line = []
	else:
		_line = drawing.diag_line(life['pos'],pos)
	
	for pos in _line:
		_x = pos[0]-CAMERA_POS[0]
		_y = pos[1]-CAMERA_POS[1]
		
		if _x<0 or _x>=MAP_WINDOW_SIZE[0] or _y<0 or _y>=MAP_WINDOW_SIZE[1]:
			continue
		
		if life['map'][pos[0]][pos[1]][CAMERA_POS[2]+1]:				
			return False
	
	return True

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
			remove_item_from_limb(life,item['id'],limb)
		
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
	
	if 'player' in life:
		menus.remove_item_from_menus({'id': item['id']})
	
	logging.debug('Removed from inventory: %s' % item['name'])
	
	del life['inventory'][str(item['id'])]
	del item['id']
	
	create_and_update_self_snapshot(life)
	
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
	
	create_and_update_self_snapshot(life)
	
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
					continue
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

#TODO: Since we are drawing in a blank area, we only need to do this once!
def draw_life_info(life):
	_info = []
	_name_mods = ''
	_holding = get_held_items(life)
	_bleeding = get_bleeding_limbs(life)
	_broken = get_broken_limbs(life)
	_bruised = get_bruised_limbs(life)
	_cut = get_cut_limbs(life)
	
	if life['asleep']:
		_name_mods = ' (Asleep)'
	
	console_set_default_foreground(0,BORDER_COLOR)
	console_print_frame(0,MAP_WINDOW_SIZE[0],0,60,WINDOW_SIZE[1]-MESSAGE_WINDOW_SIZE[1])
	
	console_set_default_foreground(0,white)
	console_print(0,MAP_WINDOW_SIZE[0]+1,0,' '.join(life['name'])+_name_mods)
	
	if _holding:
		_held_item_names = [items.get_name(get_inventory_item(life,item)) for item in _holding]
		_held_string = language.prettify_string_array(_held_item_names,max_length=BLEEDING_STRING_MAX_LENGTH)
		_info.append({'text': 'Holding: %s' % _held_string, 'color': white})
	else:
		_info.append({'text': 'You aren\'t holding anything.',
			'color': Color(125,125,125)})
	
	if _bleeding:
		_bleeding_string = language.prettify_string_array(_bleeding,max_length=BLEEDING_STRING_MAX_LENGTH)
		_info.append({'text': 'Bleeding: %s' % _bleeding_string, 'color': red})
	else:
		_info.append({'text': 'You are not bleeding.',
			'color': Color(0,200,0)})
	
	if _broken:
		_broken_string = language.prettify_string_array(_broken,max_length=BLEEDING_STRING_MAX_LENGTH)
		
		_info.append({'text': 'Broken: %s' % _broken_string,
			'color': red})
	else:
		_info.append({'text': 'You have no broken limbs.',
			'color': Color(0,200,0)})
	
	if _cut:
		_cut_string = language.prettify_string_array(_cut,max_length=BLEEDING_STRING_MAX_LENGTH)
		
		_info.append({'text': 'Cut: %s' % _cut_string,
			'color': red})
	else:
		_info.append({'text': 'You have no cut limbs.',
			'color': Color(0,200,0)})
	
	if _bruised:
		_bruised_string = language.prettify_string_array(_bruised,max_length=BLEEDING_STRING_MAX_LENGTH)
		
		_info.append({'text': 'Buised: %s' % _bruised_string,
			'color': red})
	else:
		_info.append({'text': 'You have no bruised limbs.',
			'color': Color(0,200,0)})
	
	_i = 1
	for entry in _info:
		console_set_default_foreground(0,entry['color'])
		console_print(0,MAP_WINDOW_SIZE[0]+1,_i,entry['text'])
		
		_i += 1
	
	_blood_r = numbers.clip(300-int(life['blood']),0,255)
	_blood_g = numbers.clip(int(life['blood']),0,255)
	console_set_default_foreground(0,Color(_blood_r,_blood_g,0))
	console_print(0,MAP_WINDOW_SIZE[0]+1,len(_info)+1,'Blood: %s' % life['blood'])

def pass_out(life,length=None):
	if not length:
		length = get_total_pain(life)*PASS_OUT_PAIN_MOD
	
	life['asleep'] = length
	
	if 'player' in life:
		gfx.message('You pass out!',style='damage')
	
	logging.debug('%s passed out.' % life['name'][0])

def get_total_pain(life):
	_pain = 0
	
	for limb in [life['body'][limb] for limb in life['body']]:
		_pain += limb['pain']
	
	return _pain

def calculate_blood(life):
	_blood = 0
	
	if life['blood']<=0:
		return 0
	
	for limb in [life['body'][limb] for limb in life['body']]:
		_blood += limb['bleeding']
	
	life['blood'] -= _blood*LIFE_BLEED_RATE
	
	return life['blood']

def get_limb_damage_penalty(life,limb,amount):
	"""Returns the penalty of having a pre-existing injury on a limb."""
	_limb = life['body'][limb]
	
	return int((100-_limb['condition'])*.25)	

def get_bleeding_limbs(life):
	"""Returns list of bleeding limbs."""
	_bleeding = []
	
	for limb in life['body']:
		if life['body'][limb]['bleeding']:
			_bleeding.append(limb)
	
	return _bleeding

def get_broken_limbs(life):
	"""Returns list of broken limbs."""
	_broken = []
	
	for limb in life['body']:
		if life['body'][limb]['broken']:
			_broken.append(limb)
	
	return _broken

def get_bruised_limbs(life):
	"""Returns list of bruised limbs."""
	_bruised = []
	
	for limb in life['body']:
		if life['body'][limb]['bruised']:
			_bruised.append(limb)
	
	return _bruised

def get_cut_limbs(life):
	"""Returns list of cut limbs."""
	_cut = []
	
	for limb in life['body']:
		if life['body'][limb]['cut']:
			_cut.append(limb)
	
	return _cut

def cut_limb(life,limb):
	_limb = life['body'][limb]
	
	if _limb['cut']:
		return True
	
	_limb['cut'] = True
	_limb['bleeding'] += 2
	
	if life.has_key('player'):
		gfx.message('Your %s is severely cut!' % limb,style='damage')
		
		effects.create_splatter(life,limb)

def break_limb(life,limb):
	_limb = life['body'][limb]
	
	_limb['broken'] = True
	_limb['bleeding'] += 3

def bruise_limb(life,limb):
	_limb = life['body'][limb]
	
	_limb['bruised'] = True

def add_pain_to_limb(life,limb,amount=1):
	_limb = life['body'][limb]
	
	_limb['pain'] += amount

def get_all_attached_limbs(life,limb):
	_limb = life['body'][limb]
	
	if not 'children' in _limb:
		return [limb]
	
	_attached = [limb]
	
	for child in _limb['children']:
		_attached.extend(get_all_attached_limbs(life,child))
	
	return _attached

def damage_from_fall(life,dist):
	print 'FELL',dist
	
	memory(life,'fell %s feet' % (dist*15),
		pos=life['pos'][:])
	
	if 0<dist<=3:
		if 'player' in life:
			gfx.message('You land improperly!')
			gfx.message('Your legs are bruised in the fall.',style='damage')
		
		for limbs in life['legs']:
			for leg in get_all_attached_limbs(life,limbs):
				if life['body'][leg]['bruised']:
					add_pain_to_limb(life,leg,amount=dist*2)
				else:
					memory(life,'bruised their %s in a fall' % (leg),
						pos=life['pos'][:],
						limb=leg)
					
					bruise_limb(life,leg)
					add_pain_to_limb(life,leg,amount=dist)
			
	elif dist>3:
		if 'player' in life:
			gfx.message('You hear the sound of breaking bones!')
			gfx.message('You break both legs in the fall.',style='damage')
		
		for limbs in life['legs']:
			for leg in get_all_attached_limbs(life,limbs):				
				if life['body'][leg]['broken']:
					add_pain_to_limb(life,leg,amount=dist*10)
				else:
					memory(life,'broke their %s in a fall' % (leg),
						pos=life['pos'][:],
						limb=leg)
					
					break_limb(life,leg)
					add_pain_to_limb(life,leg,amount=dist*3)
	else:
		return False
	
	create_and_update_self_snapshot(life)
	
	return True

def damage_from_item(life,item,damage):
	#TODO: I'll randomize this for now, but in the future I'll crunch the numbers
	#Here, have some help :)
	#print item['velocity']
	print 'BULLET HIT'
	_hit_type = False
	
	#We'll probably want to randomly select a limb out of a group of limbs right now...
	_rand_limb = random.choice(life['body'].keys())
	_poss_limbs = [_rand_limb]
	
	if 'parent' in life['body'][_rand_limb]:
		_poss_limbs.append(life['body'][_rand_limb]['parent'])
	
	if 'children' in life['body'][_rand_limb]:
		_poss_limbs.append(life['body'][_rand_limb]['children'][0])

	_hit_limb = random.choice(_poss_limbs)

	if item['sharp']:
		cut_limb(life,_hit_limb)
		add_pain_to_limb(life,_hit_limb,amount=12)
		_hit_type = 'cut'
	else:
		bruise_limb(life,_hit_limb)
		add_pain_to_limb(life,_hit_limb,amount=8)
		_hit_type = 'blunt'
	
	item['damage'] = damage
	_damage = item['damage']#TODO: armor here
	#_damage -= abs(item['maxvelocity'][0]-item['velocity'][0])+abs(item['maxvelocity'][1]-item['velocity'][1])
	
	life['body'][_hit_limb]['condition'] -= _damage
	
	create_and_update_self_snapshot(life)
	
	print get_total_pain(life)
	
	if life.has_key('player'):
		gfx.message('You feel a sudden force against you. (-%s)' % _damage)
	else:
		#TODO: This should be filed into the event system for the ALife's memory.
		if _hit_type == 'cut':
			say(life,'A bullet hits @n\'s %s, tearing the flesh!' % _hit_limb,action=True)
		#gfx.message('%s rips through %s\'s chest! (-%s)' % (items.get_name(item),life['name'],_damage))
		pass

def natural_healing(life):
	if life['asleep']:
		_heal_rate = 0.05
	else:
		_heal_rate = 0.03
	
	for limb in [life['body'][limb] for limb in life['body']]:
		if limb['pain'] > 4:
			limb['pain'] -= 0.05
		
		if limb['cut']:
			if limb['bleeding']>0:
				limb['bleeding'] -= 0.006
			
			if limb['bleeding']<0:
				limb['bleeding'] = 0

def tick_all_life(source_map):
	for life in LIFE:
		tick(life,source_map)
