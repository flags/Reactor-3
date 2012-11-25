from globals import *
import graphics as gfx
import pathfinding
import logging
import items
import copy
import time
import json
import os

def load_life(life):
	with open(os.path.join(LIFE_DIR,life+'.json'),'r') as e:
		return json.loads(e.readline())

def calculate_base_stats(life):
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
		
		elif flag.count('MELEE'):
			stats['melee'] = flag.partition('[')[2].partition(']')[0].split(',')
	
	stats['speed_max'] = LIFE_MAX_SPEED-(len(stats['legs']))
	
	return stats

def _get_max_speed(life,leg):
	#TODO: This will be used to calculate damage at some point...
	_speed_mod = 0
	
	for limb in leg['attached']:
		limb = get_limb(life['body'],limb)
		for item in limb['holding']:
			_i = get_inventory_item(life,item)
			
			if _i.has_key('speed_mod'):
				_speed_mod += _i['speed_mod']
		
		_speed_mod += _get_max_speed(life,limb)
	
	return _speed_mod

def get_max_speed(life):
	_speed_mod = 0
	for leg in life['legs']:
		_leg = get_limb(life['body'],leg)
		_speed_mod += _get_max_speed(life,_leg)
	
	return _speed_mod

def initiate_life(name):
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
	for limb in body:
		#Unicode fix:
		_val = body[limb].copy()
		del body[limb]
		body[str(limb)] = _val
		body[limb] = body[str(limb)]
		
		#If canhold or canstore
		body[limb]['storing'] = []
		body[limb]['holding'] = []
		initiate_limbs(body[limb]['attached'])

def get_limb(body,limb):
	_limb = []
	
	for limb1 in body:
		if limb1 == limb:
			return body[limb1]
		
		_limbs = get_limb(body[limb1]['attached'],limb)
		if _limbs:
			_limb = _limbs
	
	return _limb

def get_all_limbs(body):
	_limbs = {}
	
	for limb in body:
		_limb = body[limb].copy()
		del _limb['attached']
		
		_limbs[limb] = _limb
		_limbs.update(get_all_limbs(body[limb]['attached']))
	
	return _limbs

def attach_item_to_limb(body,item,limb):
	for limb1 in body:
		if limb1 == limb:
			body[limb1]['holding'].append(item)
			print '%s attached to %s' % (item,limb)
			return True
		
		attach_item_to_limb(body[limb1]['attached'],item,limb)

def create_life(type,position=(0,0,2),name=('Test','McChuckski'),map=None):
	if not type in LIFE_TYPES:
		raise Exception('Life type \'%s\' does not exist.' % type)
	
	#TODO: Any way to get rid of this call to `copy`?
	_life = copy.deepcopy(LIFE_TYPES[type])
	_life['name'] = name
	_life['speed'] = _life['speed_max']
	_life['pos'] = list(position)
	_life['map'] = map
	_life['path'] = []
	_life['actions'] = []
	_life['item_index'] = 0
	_life['inventory'] = {}
	_life['flags'] = {}
	
	initiate_limbs(_life['body'])
	LIFE.append(_life)
	
	return _life

def set_state(life,flag,state):
	life['flags'][flag] = state

def get_state(life,flag):
	if flag in life['flags']:
		return life['flags'][flag]
	
	raise Exception('State \'%s\' does not exist.' % flag)

def path_dest(life):
	if not life['path']:
		return None
	
	return tuple(life['path'][len(life['path'])-1])

def walk(life,to):
	if life['speed']:
		life['speed'] -= 1
		return False
	else:
		life['speed'] = life['speed_max']
	
	_dest = path_dest(life)
	
	if not _dest == tuple(to):
		#_stime = time.time()
		_path = pathfinding.astar(start=life['pos'],end=to,size=MAP_SIZE,omap=life['map'])
		life['path'] = _path.find_path(life['pos'])
		#print time.time()-_stime
	
	return walk_path(life)

def walk_path(life):
	if life['path']:
		_pos = list(life['path'].pop(0))
		life['pos'] = [_pos[0],_pos[1],life['pos'][2]]
		
		if life['path']:
			return False
		else:
			return True
	else:
		print 'here?'
		return False

def get_highest_action(life):
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
	life['actions'] = []

def add_action(life,action,score):
	_tmp_action = {'action': action,'score': score}
	if not _tmp_action in life['actions']:
		life['actions'].append(_tmp_action)
	
	return False

def perform_action(life):
	_action = get_highest_action(life)
	
	if not _action in life['actions']:
		return False

	_score = _action['score']
	_action = _action['action']
	
	if _action['action'] == 'move':
		if tuple(_action['to']) == tuple(life['pos']) or walk(life,_action['to']):
			life['actions'].remove({'action':_action,'score':_score})

def tick(life):
	perform_action(life)

def get_inventory_item(life,id):
	if not life['inventory'].has_key(str(id)):
		raise Exception('Life \'%s\' does not have item of id #%s'
			% (life['name'][0],id))
	
	return life['inventory'][str(id)]

def add_item_to_inventory(life,item):
	_id = life['item_index']
	item['id'] = _id
	life['inventory'][str(_id)] = item
	life['item_index'] += 1
	
	print '%s got \'%s\'.' % (life['name'][0],item['name'])
	
	return _id

def equip_item(life,id):
	_limbs = get_all_limbs(life['body'])
	item = get_inventory_item(life,id)
	
	#TODO: Faster way to do this with sets
	for limb in item['attaches_to']:
		if not limb in _limbs:
			print 'Limb not found:',limb
			return False
	
	print '%s puts on a %s' % (life['name'][0],item['name'])
	
	for limb in item['attaches_to']:
		attach_item_to_limb(life['body'],item['id'],limb)
	
	life['speed_max'] = life['speed_max']-get_max_speed(life)
	if life['speed'] > life['speed_max']:
		life['speed'] = life['speed_max']

def pick_up_item_from_ground(life,item):
	for _item in items.get_items_at(life['pos']):
		if _item['name'] == item:
			add_item_to_inventory(life,_item)
			return True
		
	raise Exception('Item \'%s\' does not exist at (%s,%s,%s).'
		% (item,life['pos'][0],life['pos'][1],life['pos'][2]))

def item_is_equipped(life,item):
	for _limb in get_all_limbs(life['body']):
		if int(item) in get_limb(life['body'],_limb)['holding']:
			return True
	
	return False

def show_life_info(life):
	for key in life:
		if key == 'body':
			continue
		
		print '%s: %s' % (key,life[key])
	
	return True

def draw_life():
	for life in LIFE:
		if not life['pos'][2] <= CAMERA_POS[2]:
			continue
		
		if life['pos'][0] >= CAMERA_POS[0] and life['pos'][0] < CAMERA_POS[0]+MAP_WINDOW_SIZE[0] and\
			life['pos'][1] >= CAMERA_POS[1] and life['pos'][1] < CAMERA_POS[1]+MAP_WINDOW_SIZE[1]:
			_x = life['pos'][0] - CAMERA_POS[0]
			_y = life['pos'][1] - CAMERA_POS[1]
			gfx.blit_char(_x,_y,life['icon'],white,None)

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

#Conductor
def tick_all_life():
	for life in LIFE:
		tick(life)
