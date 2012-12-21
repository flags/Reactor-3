"""Reactor 3"""
from libtcodpy import *
from globals import *
from inputs import *
from tiles import *
import graphics as gfx
import maputils
import logging
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

#Optional Cython-compiled modules
try:
	import render_map
	
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

PLACING_TILE = WALL_TILE

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	"""Parses input."""
	if gfx.window_is_closed():
		RUNNING = False
	
	if INPUT['\x1b'] or INPUT['q']:
		if ACTIVE_MENU['menu'] >= 0:
			menus.delete_menu(ACTIVE_MENU['menu'])
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
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0],PLAYER['pos'][1]-1)},200)

	if INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			MENUS[ACTIVE_MENU['menu']]['index'] = menus.find_item_after(MENUS[ACTIVE_MENU['menu']],index=MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0],PLAYER['pos'][1]+1)},200)

	if INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0]+1,PLAYER['pos'][1])},200)

	if INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
		else:
			life.clear_actions(PLAYER)
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0]-1,PLAYER['pos'][1])},200)
	
	if INPUT['i']:
		if menus.get_menu_by_name('Inventory')>-1:
			menus.delete_menu(menus.get_menu_by_name('Inventory'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(PLAYER)
		
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
		
		_inventory = []
		for entry in PLAYER['inventory']:
			item = life.get_inventory_item(PLAYER,entry)
			
			if not life.item_is_equipped(PLAYER,entry):
				_menu_item = menus.create_item('single',
					item['name'],
					'Not equipped',
					icon=item['icon'],
					id=int(entry))
				
				_inventory.append(_menu_item)
		
		if not _inventory:
			gfx.message('You have no items to equip.')
			return False
		
		_i = menus.create_menu(title='Equip',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_equip)
		
		menus.activate_menu(_i)
	
	if INPUT['d']:
		if menus.get_menu_by_name('Drop')>-1:
			menus.delete_menu(menus.get_menu_by_name('Drop'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(PLAYER)
		
		_i = menus.create_menu(title='Drop',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_drop)
		
		menus.activate_menu(_i)
	
	if INPUT[',']:
		_items = items.get_items_at(PLAYER['pos'])
		
		if not _items:
			return False
		
		create_pick_up_item_menu(_items)
	
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

def move_camera():
	if PLAYER['pos'][1]<CAMERA_POS[1]+MAP_WINDOW_SIZE[1]/2 and CAMERA_POS[1]>0:
		CAMERA_POS[1] -= 1
	
	elif PLAYER['pos'][1]-CAMERA_POS[1]>MAP_WINDOW_SIZE[1]/2:
		CAMERA_POS[1] += 1
	
	elif PLAYER['pos'][0]-CAMERA_POS[0]>MAP_WINDOW_SIZE[0]/2:
		CAMERA_POS[0]+=1
	
	elif PLAYER['pos'][0]<CAMERA_POS[0]+MAP_WINDOW_SIZE[0]/2 and CAMERA_POS[0]>0:
		CAMERA_POS[0] -= 1
	
	CAMERA_POS[2] = PLAYER['pos'][2]

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
	
	_name = items.get_name(life.get_inventory_item(PLAYER,item))
	
	if life.equip_item(PLAYER,int(item)):
		_stored = life.item_is_stored(PLAYER,int(item))
		if _stored:
			gfx.message('You remove %s from your %s.' % (_name,_stored['name']))
		
		gfx.message('You put on %s.' % _name)
	
		menus.delete_menu(ACTIVE_MENU['menu'])
	else:
		gfx.message('You can\'t wear %s.' % _name)

def inventory_drop(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['id']
	
	_name = items.get_name(life.get_inventory_item(PLAYER,item))
	
	if life.item_is_equipped(PLAYER,item):
		gfx.message('You take off %s.' % _name)
			
	_stored = life.item_is_stored(PLAYER,item)
	if _stored:
		_item = life.get_inventory_item(PLAYER,item)
		gfx.message('You remove %s from your %s.' % (_name,_stored['name']))
	
	gfx.message('You drop %s.' % _name)
	life.drop_item(PLAYER,item)
	
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
				'item': entry['item'],
				'life': PLAYER},
				200,
				delay=40)
		
		elif entry['values'][entry['value']] in PLAYER['hands']:
			gfx.message('You start to pick up %s.' % items.get_name(entry['item']))
			
			life.add_action(PLAYER,{'action': 'pickupholditem',
				'item': entry['item'],
				'hand': entry['values'][entry['value']],
				'life': PLAYER},
				200,
				delay=40)
		
		return True
	
	gfx.message('You start to put %s in your %s.' %
		(items.get_name(entry['item']),entry['container']['name']))
	
	life.add_action(PLAYER,{'action': 'pickupitem',
		'item': entry['item'],
		'container': entry['container'],
		'life': PLAYER},
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
		_menu.append(menus.create_item('single',
			container['name'],
			'%s/%s' % (container['capacity'],container['max_capacity']),
			container=container,
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

LIGHTS.append({'x': 40,'y': 30,'brightness': 40.0})

SETTINGS['draw z-levels below'] = True
SETTINGS['draw z-levels above'] = True

life.initiate_life('Human')
_test = life.create_life('Human',name=['derp','yerp'],map=MAP)
#life.add_action(_test,{'action': 'move', 'to': (50,0)},200)
PLAYER = life.create_life('Human',name=['derp','yerp'],map=MAP,position=[15,20,4])
PLAYER['player'] = True

items.initiate_item('white_shirt')
items.initiate_item('sneakers')
items.initiate_item('leather_backpack')
items.initiate_item('blue_jeans')

_i1 = items.create_item('white t-shirt',MAP)
_i2 = items.create_item('sneakers',MAP)
_i3 = items.create_item('sneakers',MAP)
_i4 = items.create_item('sneakers',MAP,position=(8,15,2))
_i4 = items.create_item('white t-shirt',MAP,position=(5,20,2))
_i5 = items.create_item('leather backpack',MAP)
_i6 = items.create_item('blue jeans',MAP)

items.move(_i4,[0.5,0,1])

life.add_item_to_inventory(PLAYER,_i1)
life.add_item_to_inventory(PLAYER,_i2)
life.add_item_to_inventory(PLAYER,_i3)
life.add_item_to_inventory(PLAYER,_i5)
life.add_item_to_inventory(PLAYER,_i6)

CURRENT_UPS = UPS

while RUNNING:
	get_input()
	handle_input()
	_played_moved = False

	while life.get_highest_action(PLAYER):
		items.tick_all_items()
		life.tick_all_life()
		_played_moved = True
		
		if CURRENT_UPS:
			CURRENT_UPS-=1
		else:
			CURRENT_UPS = UPS
			break
	
	if not _played_moved:
		items.tick_all_items()
		life.tick_all_life()
	
	gfx.start_of_frame()
	
	if CYTHON_ENABLED:
		render_map.render_map(MAP)
	else:
		maps.render_map(MAP)
	
	maps.render_lights()
	items.draw_items()
	move_camera()
	maps.render_los(MAP,PLAYER['pos'])
	life.draw_life()
	life.draw_visual_inventory(PLAYER)
	menus.align_menus()
	menus.draw_menus()
	gfx.draw_bottom_ui()
	gfx.draw_console()
	gfx.end_of_frame_reactor3()
	gfx.end_of_frame()

maps.save_map('map1.dat',MAP)
