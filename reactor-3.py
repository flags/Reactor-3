"""Reactor 3"""
from libtcodpy import *
from globals import *
from inputs import *
from tiles import *
import graphics as gfx
import maputils
import drawing
import logging
import weapons
import numbers
import bullets
import random
import menus
import items
import life
import time
import maps
import sys

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('[%(asctime)s-%(levelname)s] %(message)s',datefmt='%H:%M:%S %m/%d/%y')
ch = logging.StreamHandler()
ch.setFormatter(console_formatter)
logger.addHandler(ch)

#TODO: Replace with "module_sanity_check"
#Optional Cython-compiled modules
try:
	import render_map
	import render_los
	
	if render_map.VERSION == MAP_RENDER_VERSION:
		CYTHON_ENABLED = True
	else:
		CYTHON_ENABLED = False
		logging.warning('[Cython] render_map is out of date!')
		logging.warning('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')
	
except ImportError, e:
	CYTHON_ENABLED = False
	logging.warning('[Cython] ImportError with module: %s' % e)
	logging.warning('[Cython] Certain functions can run faster if compiled with Cython.')
	logging.warning('[Cython] Run \'python compile_cython_modules.py build_ext --inplace\'')

gfx.log(WINDOW_TITLE)

try:
	MAP = maps.load_map('map1.dat')
except IOError:
	MAP = maps.create_map()
	maps.save_map(MAP)

gfx.init_libtcod()
create_all_tiles()

PLACING_TILE = WALL_TILE

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	if gfx.window_is_closed():
		RUNNING = False
		
		return True
	
	if INPUT['\x1b'] or INPUT['q']:
		if ACTIVE_MENU['menu'] >= 0:
			menus.delete_menu(ACTIVE_MENU['menu'])
		elif PLAYER['targetting']:
			PLAYER['targetting'] = None
			PLAYER['throwing'] = None
			PLAYER['firing'] = None
			SELECTED_TILES[0] = []
		else:
			RUNNING = False
	
	if INPUT['-']:
		if SETTINGS['draw console']:
			SETTINGS['draw console'] = False
		else:
			SETTINGS['draw console'] = True
	
	if SETTINGS['draw console']:
		return

	if INPUT['up']:
		if not ACTIVE_MENU['menu'] == -1:
			MENUS[ACTIVE_MENU['menu']]['index'] = menus.find_item_before(MENUS[ACTIVE_MENU['menu']],index=MENUS[ACTIVE_MENU['menu']]['index'])
		elif PLAYER['targetting']:
			PLAYER['targetting'][1]-=1
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0],PLAYER['pos'][1]-1)},200)

	if INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			MENUS[ACTIVE_MENU['menu']]['index'] = menus.find_item_after(MENUS[ACTIVE_MENU['menu']],index=MENUS[ACTIVE_MENU['menu']]['index'])
		elif PLAYER['targetting']:
			PLAYER['targetting'][1]+=1
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0],PLAYER['pos'][1]+1)},200)

	if INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
		elif PLAYER['targetting']:
			PLAYER['targetting'][0]+=1
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0]+1,PLAYER['pos'][1])},200)

	if INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
		elif PLAYER['targetting']:
			PLAYER['targetting'][0]-=1
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0]-1,PLAYER['pos'][1])},200)
	
	if INPUT['i']:
		if menus.get_menu_by_name('Inventory')>-1:
			menus.delete_menu(menus.get_menu_by_name('Inventory'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(PLAYER,check_hands=True)
		
		if not _inventory:
			gfx.message('You have no items.')
			return False
		
		_i = menus.create_menu(title='Inventory',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_select)
		
		menus.activate_menu(_i)
	
	if INPUT['e']:
		if menus.get_menu_by_name('Equip')>-1:
			menus.delete_menu(menus.get_menu_by_name('Equip'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(PLAYER,show_equipped=False,check_hands=False)
		
		if not _inventory:
			gfx.message('You have no items to equip.')
			return False
		
		_i = menus.create_menu(title='Equip',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k',
			on_select=inventory_equip)
		
		menus.activate_menu(_i)
	
	if INPUT['d']:
		if menus.get_menu_by_name('Drop')>-1:
			menus.delete_menu(menus.get_menu_by_name('Drop'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(PLAYER,check_hands=True)
		
		_i = menus.create_menu(title='Drop',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_drop)
		
		menus.activate_menu(_i)
	
	if INPUT['t']:
		if menus.get_menu_by_name('Throw')>-1:
			menus.delete_menu(menus.get_menu_by_name('Throw'))
			return False
		
		if PLAYER['targetting']:
			life.throw_item(PLAYER,PLAYER['throwing']['id'],PLAYER['targetting'],1)
			PLAYER['targetting'] = None
			SELECTED_TILES[0] = []
			return True
		
		_throwable = life.get_fancy_inventory_menu_items(PLAYER,show_equipped=False,check_hands=True)
		
		_i = menus.create_menu(title='Throw',
			menu=_throwable,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_throw)
		
		menus.activate_menu(_i)
	
	if INPUT['f']:
		if menus.get_menu_by_name('Fire')>-1:
			menus.delete_menu(menus.get_menu_by_name('Fire'))
			return False
		
		if PLAYER['targetting']:
			weapons.fire(PLAYER,PLAYER['targetting'])
			PLAYER['targetting'] = None
			SELECTED_TILES[0] = []
			return True
		
		#TODO: Pause game
		
		_weapons = []
		for hand in PLAYER['hands']:
			_limb = life.get_limb(PLAYER['body'],hand)
			
			if not _limb['holding']:
				continue
			
			_item = life.get_inventory_item(PLAYER,_limb['holding'][0])
			
			if _item['type'] == 'gun':
				_weapons.append(menus.create_item('single',
					_item['name'],
					'Temp',
					icon=_item['icon'],
					id=_item['id']))
		
		if not _weapons:
			gfx.message('You have nothing to shoot!')
			return False
		
		_i = menus.create_menu(title='Fire',
			menu=_weapons,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_fire)
		
		menus.activate_menu(_i)
	
	if INPUT['r']:
		if menus.get_menu_by_name('Reload')>-1:
			menus.delete_menu(menus.get_menu_by_name('Reload'))
			return False
		
		_menu = []
		_loaded_weapons = []
		_unloaded_weapons = []
		_non_empty_ammo = []
		_empty_ammo = []
		
		for weapon in life.get_all_inventory_items(PLAYER,matches=[{'type': 'gun'}]):
			_feed = weapons.get_feed(weapon)
			
			if _feed:
				_loaded_weapons.append(menus.create_item('single',
					weapon['name'],
					'%s/%s' % (len(_feed['rounds']),_feed['maxrounds']),
					icon=weapon['icon'],
					id=weapon['id']))
			else:
				_unloaded_weapons.append(menus.create_item('single',
					weapon['name'],
					'Empty',
					icon=weapon['icon'],
					id=weapon['id']))
		
		for ammo in life.get_all_inventory_items(PLAYER,matches=[{'type': 'magazine'},{'type': 'clip'}]):
			#TODO: Make `parent` an actual key.
			if 'parent' in ammo:
				continue
			
			if ammo['rounds']:
				_non_empty_ammo.append(menus.create_item('single',
					ammo['name'],
					'%s/%s' % (len(ammo['rounds']),ammo['maxrounds']),
					icon=ammo['icon'],
					id=ammo['id']))
			else:
				_empty_ammo.append(menus.create_item('single',
					ammo['name'],
					'%s/%s' % (len(ammo['rounds']),ammo['maxrounds']),
					icon=ammo['icon'],
					id=ammo['id']))
			
		if _loaded_weapons:
			_menu.append(menus.create_item('title','Loaded weapons',None))
			_menu.extend(_loaded_weapons)
		
		#TODO: Disabled for now.
		#if _unloaded_weapons:
		#	_menu.append(menus.create_item('title','Unloaded weapons',None))
		#	_menu.extend(_unloaded_weapons)
			
		if _non_empty_ammo:
			_menu.append(menus.create_item('title','Mags/Clips (Non-empty)',None))
			_menu.extend(_non_empty_ammo)
		
		if _empty_ammo:
			_menu.append(menus.create_item('title','Mags/Clips (Empty)',None))
			_menu.extend(_empty_ammo)
		
		if not _menu:
			gfx.message('You have no ammo!')
			return False
		
		_i = menus.create_menu(title='Reload',
			menu=_menu,
			padding=(1,1),
			position=(1,1),
			format_str='$k: $v',
			on_select=inventory_reload)
		
		menus.activate_menu(_i)
	
	if INPUT['o']:
		if menus.get_menu_by_name('Options')>-1:
			menus.delete_menu(menus.get_menu_by_name('Options'))
			return False
		
		_options = []
		_options.append(menus.create_item('title','Debug (Developer)',None))
		_options.append(menus.create_item('spacer','=',None))
		_options.append(menus.create_item('single','Reload map','Reloads map from disk'))
		
		_i = menus.create_menu(title='Options',
			menu=_options,
			padding=(1,1),
			position=(1,1),
			format_str='$k: $v',
			on_select=handle_options_menu)
		
		menus.activate_menu(_i)
	
	if INPUT[',']:
		_items = items.get_items_at(PLAYER['pos'])
		
		if not _items:
			return False
		
		create_pick_up_item_menu(_items)
	
	if INPUT['b']:
		print life.create_recent_history(SETTINGS['following'])
	
	if INPUT['y']:
		if LIFE.index(SETTINGS['following'])<len(LIFE)-1:
			SETTINGS['following'] = LIFE[LIFE.index(SETTINGS['following'])+1]

	if INPUT['u']:
		if LIFE.index(SETTINGS['following'])>0:
			SETTINGS['following'] = LIFE[LIFE.index(SETTINGS['following'])-1]
	
	if INPUT['\r']:
		if ACTIVE_MENU['menu'] == -1:
			return False
		
		menus.item_selected(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])

	if INPUT['l']:
		SUN_BRIGHTNESS[0] += 4
	
	if INPUT['k']:
		SUN_BRIGHTNESS[0] -= 4

	if INPUT['1']:
		CAMERA_POS[2] = 1

	if INPUT['2']:
		CAMERA_POS[2] = 2

	if INPUT['3']:
		CAMERA_POS[2] = 3

	if INPUT['4']:
		CAMERA_POS[2] = 4

	if INPUT['5']:
		CAMERA_POS[2] = 5

def move_camera(pos,scroll=False):
	
	CAMERA_POS[0] = numbers.clip(pos[0]-(MAP_WINDOW_SIZE[0]/2),0,MAP_SIZE[0]-MAP_WINDOW_SIZE[0])
	CAMERA_POS[1] = numbers.clip(pos[1]-(MAP_WINDOW_SIZE[1]/2),0,MAP_SIZE[1]-MAP_WINDOW_SIZE[1])
	CAMERA_POS[2] = pos[2]
	
	return False
	#TODO: Scrolling!
	#if pos[1]<CAMERA_POS[1]+MAP_WINDOW_SIZE[1]/2 and CAMERA_POS[1]>0:
		#if snap:
			#CAMERA_POS[1] = CAMERA_POS[1]+MAP_WINDOW_SIZE[1]/2
		#else:
			#CAMERA_POS[1] -= 1
	
	#elif pos[1]-CAMERA_POS[1]>MAP_WINDOW_SIZE[1]/2 and CAMERA_POS[1]+MAP_WINDOW_SIZE[1]<MAP_SIZE[1]:
		#if snap:
			#CAMERA_POS[1] = CAMERA_POS[1]+MAP_WINDOW_SIZE[1]/2
		#else:
			#CAMERA_POS[1] += 1
	
	#if pos[0]-CAMERA_POS[0]>MAP_WINDOW_SIZE[0]/2 and CAMERA_POS[0]+MAP_WINDOW_SIZE[0]<MAP_SIZE[0]:
		#CAMERA_POS[0]+=1
	
	#elif pos[0]<CAMERA_POS[0]+MAP_WINDOW_SIZE[0]/2 and CAMERA_POS[0]>0:
		#CAMERA_POS[0] -= 1
	
	#CAMERA_POS[2] = pos[2]

def draw_targetting():
	if PLAYER['targetting']:
		
		SELECTED_TILES[0] = []
		for pos in drawing.diag_line(PLAYER['pos'],PLAYER['targetting']):
			SELECTED_TILES[0].append((pos[0],pos[1],PLAYER['pos'][2]))

def handle_options_menu(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Reload map':
		logging.warning('Map reloading is not well tested!')
		global MAP
		del MAP
		
		MAP = maps.load_map('map1.dat')
		
		logging.warning('Updating references to map. This may take a while.')
		for entry in LIFE:
			entry['map'] = MAP
		
		logging.warning('Redrawing LOS.')
		maps._render_los(MAP,PLAYER['pos'],cython=CYTHON_ENABLED)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_select(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_menu_items = []
	
	for _key in ITEM_TYPES[key]:
		_menu_items.append(menus.create_item('single',_key,ITEM_TYPES[key][_key]))
	
	_i = menus.create_menu(title=key,
		menu=_menu_items,
		padding=(1,1),
		position=(1,1),
		on_select=return_to_inventory,
		dim=False)
		
	menus.activate_menu(_i)

def inventory_equip(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['id']
	
	_item = life.get_inventory_item(PLAYER,item)
	
	if _item['type'] == 'gun' and not life.can_hold_item(PLAYER):
		gfx.message('You can\'t possibly hold that!')
		
		return False
	
	life.add_action(PLAYER,{'action': 'equipitem',
		'item': item},
		200,
		delay=40)
	
	gfx.message('You start putting on %s.' % _item['name'])
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_drop(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['id']
	
	_name = items.get_name(life.get_inventory_item(PLAYER,item))
	
	life.add_action(PLAYER,{'action': 'dropitem',
		'item': item},
		200,
		delay=20)
	
	gfx.message('You start to drop %s.' % _name)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_throw(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(PLAYER,entry['id'])
	
	_hand = life.is_holding(PLAYER,entry['id'])
	if _hand:
		PLAYER['targetting'] = PLAYER['pos'][:]
		PLAYER['throwing'] = item
		menus.delete_menu(ACTIVE_MENU['menu'])
		
		return True
	
	_hand = life.can_throw(PLAYER)
	if not _hand:
		gfx.message('Both of your hands are full.')
	
		menus.delete_menu(ACTIVE_MENU['menu'])
		return False

	_stored = life.item_is_stored(PLAYER,item['id'])
	if _stored:
		_delay = 40
		gfx.message('You start to remove %s from your %s.' % (item['name'],_stored['name']))
	else:
		_delay = 20
	
	PLAYER['throwing'] = item
	
	life.add_action(PLAYER,{'action': 'holditemthrow',
		'item': entry['id'],
		'hand': _hand},
		200,
		delay=_delay)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_fire(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(PLAYER,entry['id'])
	
	PLAYER['firing'] = item
	
	if not life.is_holding(PLAYER,entry['id']):
		_hand = life.can_throw(PLAYER)
		if not _hand:
			gfx.message('Both of your hands are full.')
		
			menus.delete_menu(ACTIVE_MENU['menu'])
			return False
	
	PLAYER['targetting'] = PLAYER['pos'][:]
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_reload(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(PLAYER,entry['id'])
	
	if item['type'] == 'gun':
		_menu = []
		
		if weapons.get_feed(item):
			_menu.append(menus.create_item('single','Remove feed',None,id=entry['id']))
		
		_menu.append(menus.create_item('single','Insert feed',None,id=entry['id']))
		
		_i = menus.create_menu(title=key,
			menu=_menu,
			padding=(1,1),
			position=(1,1),
			on_select=inventory_handle_feed,
			format_str='$k')
	
	else:
		_menu = []
		_menu.append(menus.create_item('single','Fill',None,id=entry['id']))
		
		_weapons = []
		for _weapon in life.get_held_items(PLAYER,matches=[{'type': 'gun','ammotype': item['ammotype'],'feed': item['type']}]):
			weapon = life.get_inventory_item(PLAYER,_weapon)
			
			if weapons.get_feed(weapon):
				continue
			
			_weapons.append(menus.create_item('single',weapon['name'],None,ammo=item,id=weapon['id']))
		
		if _weapons:
			_menu.append(menus.create_item('title','Load into',None,id=entry['id']))
			_menu.extend(_weapons)
		
		_i = menus.create_menu(title=key,
			menu=_menu,
			padding=(1,1),
			position=(1,1),
			on_select=inventory_handle_ammo,
			format_str='$k')
	
	menus.activate_menu(_i)

def inventory_handle_feed(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(PLAYER,entry['id'])
	
	if key == 'Remove feed':
		life.add_action(PLAYER,{'action': 'unload',
			'weapon': item},
			200,
			delay=20)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_handle_ammo(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(PLAYER,entry['id'])
	
	if key == 'Fill':
		if not life.can_hold_item(PLAYER):
			gfx.message('You need a hand free to fill the %s with %s rounds.' % (item['type'],item['ammotype']))
			return False
		
		_hold = life.add_action(PLAYER,{'action': 'removeandholditem',
			'item': item['id']},
			200,
			delay=20)
		
		gfx.message('You start filling the %s with %s rounds.' % (item['type'],item['ammotype']))
	
		_rounds = len(item['rounds'])
		for ammo in life.get_all_inventory_items(PLAYER,matches=[{'type': 'bullet', 'ammotype': item['ammotype']}]):
			life.add_action(PLAYER,{'action': 'refillammo',
				'ammo': item,
				'round': ammo},
				200,
				delay=20)
			
			_rounds += 1
			
			if _rounds>=item['maxrounds']:
				break
	else:
		life.add_action(PLAYER,{'action': 'reload',
			'weapon': item,
			'ammo': entry['ammo']},
			200,
			delay=20)
	
	#TODO: Don't breathe this!
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_fill_ammo(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(PLAYER,entry['id'])
	
	gfx.message('You start filling the %s with %s rounds.' % (item['type'],item['ammotype']))
	
	_rounds = len(item['rounds'])
	for ammo in life.get_all_inventory_items(PLAYER,matches=[{'type': 'bullet', 'ammotype': item['ammotype']}]):
		life.add_action(PLAYER,{'action': 'refillammo',
			'ammo': item,
			'round': ammo},
			200,
			delay=20)
		
		_rounds += 1
		
		if _rounds>=item['maxrounds']:
			break
	
	#TODO: Don't breathe this!
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def pick_up_item_from_ground(entry):	
	_items = items.get_items_at(PLAYER['pos'])
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])
	
	#TODO: Lowercase menu keys
	if entry['key'] == 'Equip':
		if entry['values'][entry['value']] == 'Wear':
			gfx.message('You start to pick up %s.' % items.get_name(entry['item']))
			
			life.add_action(PLAYER,{'action': 'pickupequipitem',
				'item': entry['item']},
				200,
				delay=40)
		
		elif entry['values'][entry['value']] in PLAYER['hands']:
			gfx.message('You start to pick up %s.' % items.get_name(entry['item']))
			
			life.add_action(PLAYER,{'action': 'pickupholditem',
				'item': entry['item'],
				'hand': entry['values'][entry['value']]},
				200,
				delay=40)
		
		return True
	
	gfx.message('You start to put %s in your %s.' %
		(items.get_name(entry['item']),entry['container']['name']))
	
	life.add_action(PLAYER,{'action': 'pickupitem',
		'item': entry['item'],
		'container': entry['container']},
		200,
		delay=60)
	
	return True

def pick_up_item_from_ground_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_item = items.get_item_from_uid(entry['item'])
	
	_menu = []
	#TODO: Can we equip this?
	_menu.append(menus.create_item('title','Actions',None,enabled=False))
	_menu.append(menus.create_item('single','Equip','Wear',item=_item))
	
	for hand in PLAYER['hands']:
		_menu.append(menus.create_item('single','Equip',hand,item=_item))
	
	_menu.append(menus.create_item('title','Store in...',None,enabled=False))
	for container in life.get_all_storage(PLAYER):		
		if container['capacity']+_item['size'] > container['max_capacity']:
			_enabled = False
		else:
			_enabled = True
		
		_menu.append(menus.create_item('single',
			container['name'],
			'%s/%s' % (container['capacity'],container['max_capacity']),
			container=container,
			enabled=_enabled,
			item=_item))
	
	_i = menus.create_menu(title='Pick up (action)',
		menu=_menu,
		padding=(1,1),
		position=(1,1),
		format_str='  $k: $v',
		on_select=pick_up_item_from_ground)
		
	menus.activate_menu(_i)

def create_pick_up_item_menu(items):
	_menu_items = []
	
	for item in items:
		_menu_items.append(menus.create_item('single',0,item['name'],icon=item['icon'],item=item['uid']))
	
	_i = menus.create_menu(title='Pick up',
		menu=_menu_items,
		padding=(1,1),
		position=(1,1),
		format_str='[$i] $k: $v',
		on_select=pick_up_item_from_ground_action)
	
	menus.activate_menu(_i)

def return_to_inventory(entry):
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.activate_menu_by_name('Inventory')

def tick_all_objects():
	items.tick_all_items(MAP)
	life.tick_all_life(MAP)
	bullets.tick_bullets(MAP)

LIGHTS.append({'x': 40,'y': 30,'brightness': 40.0})

SETTINGS['draw z-levels below'] = True
SETTINGS['draw z-levels above'] = True

life.initiate_life('Human')
_test = life.create_life('Human',name=['test1',''],map=MAP,position=[50,40,2])
_test2 = life.create_life('Human',name=['test2',''],map=MAP,position=[50,50,2])
PLAYER = life.create_life('Human',name=['Tester','Toaster'],map=MAP,position=[10,10,2])
PLAYER['player'] = True

SETTINGS['following'] = _test

items.initiate_item('white_shirt')
items.initiate_item('sneakers')
items.initiate_item('leather_backpack')
items.initiate_item('blue_jeans')
items.initiate_item('glock')
items.initiate_item('9x19mm_mag')
items.initiate_item('9x19mm_round')

_i1 = items.create_item('white t-shirt')
_i2 = items.create_item('sneakers')
_i3 = items.create_item('sneakers')
_i4 = items.create_item('sneakers',position=(8,15,2))
_i4_ = items.create_item('white t-shirt',position=(5,20,2))
_i5 = items.create_item('leather backpack')
_i6 = items.create_item('blue jeans')
_i7 = items.create_item('glock')
_i8 = items.create_item('9x19mm magazine')
_i9 = items.create_item('sneakers')
_i10 = items.create_item('leather backpack')
_i11 = items.create_item('glock')
_i12 = items.create_item('9x19mm magazine')
_i13 = items.create_item('leather backpack')
_i14 = items.create_item('sneakers')

items.move(_i4,0,1,_velocity=1)
items.move(_i4_,0,1,_velocity=1)

life.add_item_to_inventory(PLAYER,_i1)
life.add_item_to_inventory(PLAYER,_i2)
life.add_item_to_inventory(PLAYER,_i3)
life.add_item_to_inventory(PLAYER,_i5)
life.add_item_to_inventory(PLAYER,_i6)
life.add_item_to_inventory(PLAYER,_i7)
life.add_item_to_inventory(PLAYER,_i8)
life.add_item_to_inventory(_test,_i9)
life.add_item_to_inventory(_test,_i10)
life.add_item_to_inventory(_test,_i11)
life.add_item_to_inventory(_test,_i12)
#life.add_item_to_inventory(_test2,_i14)
life.add_item_to_inventory(_test2,_i13)

for i in range(17):
	life.add_item_to_inventory(PLAYER,items.create_item('9x19mm round'))

for i in range(21):
	life.add_item_to_inventory(_test,items.create_item('9x19mm round'))

CURRENT_UPS = UPS

while RUNNING:
	get_input()
	handle_input()
	_played_moved = False

	while life.get_highest_action(PLAYER):
		tick_all_objects()
		_played_moved = True
		
		if CURRENT_UPS:
			CURRENT_UPS-=1
		else:
			CURRENT_UPS = UPS
			break
	
	if not _played_moved:
		tick_all_objects()
	
	draw_targetting()
	
	if CYTHON_ENABLED:
		render_map.render_map(MAP)
	else:
		maps.render_map(MAP)
	
	maps.render_lights()
	items.draw_items()
	bullets.draw_bullets()
	move_camera(SETTINGS['following']['pos'])
	life.draw_life()
	
	LOS_BUFFER[0] = maps._render_los(MAP,SETTINGS['following']['pos'],cython=CYTHON_ENABLED)
	
	if PLAYER['dead']:
		gfx.fade_to_white(FADE_TO_WHITE[0])
		_col = 255-int(round(FADE_TO_WHITE[0]))*2
		
		if _col<0:
			_col = 0
		
		_string = 'You die.'
		
		gfx.blit_string(MAP_WINDOW_SIZE[0]/2-(len(_string)/2),
			MAP_WINDOW_SIZE[1]/2,
			_string,
			console=MAP_WINDOW,
			fore_color=Color(255,_col,_col),
			back_color=Color(255-_col,255-_col,255-_col),
			flicker=0)
		FADE_TO_WHITE[0] += 0.9
	
	life.draw_life_info(PLAYER)
	menus.align_menus()
	menus.draw_menus()
	gfx.draw_message_box()
	gfx.draw_console()
	#gfx.draw_dijkstra_heatmap()
	gfx.start_of_frame()
	gfx.end_of_frame_reactor3()
	gfx.end_of_frame()
