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

#Optional Cython-compiled modules
try:
	import render_map
	CYTHON_ENABLED = True
except ImportError, e:
	CYTHON_ENABLED = False
	print '[Cython] ImportError with module: %s' % e
	print '[Cython] Certain functions can run faster if compiled with Cython.'
	print '[Cython] Run \'python compile_cython_modules.py build_ext --inplace\''

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
			if ACTIVE_MENU['index']>0:
				ACTIVE_MENU['index'] -= 1
			else:
				ACTIVE_MENU['index'] = len(MENUS[ACTIVE_MENU['menu']]['menu'])-1
		else:
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0],PLAYER['pos'][1]-1)},200)

	if INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			if ACTIVE_MENU['index']<len(MENUS[ACTIVE_MENU['menu']]['menu'])-1:
				ACTIVE_MENU['index'] += 1
			else:
				ACTIVE_MENU['index'] = 0
		else:
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0],PLAYER['pos'][1]+1)},200)

	if INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],ACTIVE_MENU['index'])
		else:
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0]+1,PLAYER['pos'][1])},200)

	if INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],ACTIVE_MENU['index'])
		else:
			life.add_action(PLAYER,{'action': 'move', 'to': (PLAYER['pos'][0]-1,PLAYER['pos'][1])},200)
	
	if INPUT['i']:
		if menus.get_menu_by_name('Inventory')>-1:
			menus.delete_menu(menus.get_menu_by_name('Inventory'))
			return False
		
		_inventory = []
		for entry in PLAYER['inventory']:
			item = life.get_inventory_item(PLAYER,entry)
			
			if life.item_is_equipped(PLAYER,entry):
				_menu_item = menus.create_item('single',item['name'],'Equipped',icon=item['icon'])
			else:
				_menu_item = menus.create_item('single',item['name'],'Not equipped',icon=item['icon'])
			
			_inventory.append(_menu_item)
		
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
				_inventory.append(menus.create_item('single',item['name'],'Not equipped',icon=item['icon']))
		
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
		
		_inventory = []
		for entry in PLAYER['inventory']:
			item = life.get_inventory_item(PLAYER,entry)
			
			if life.item_is_equipped(PLAYER,entry):
				_menu_item = menus.create_item('single',item['name'],
					'Equipped',
					icon=item['icon'],
					id=item['id'])
			else:
				_menu_item = menus.create_item('single',
					item['name'],
					'Not equipped',
					id=item['id'],
					icon=item['icon'])
			
			_inventory.append(_menu_item)
		
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
		
		menus.item_selected(ACTIVE_MENU['menu'],ACTIVE_MENU['index'])

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
	
	for item in PLAYER['inventory']:
		_name = life.get_inventory_item(PLAYER,item)['name']
		if _name == key:
			gfx.message('You put on the %s.' % _name)
			life.equip_item(PLAYER,item)
			break
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_drop(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['id']
	
	#for item in PLAYER['inventory']:
	#	_name = life.get_inventory_item(PLAYER,item)['name']
	#	if _name == key:
	_name = life.get_inventory_item(PLAYER,item)['name']
	
	if life.item_is_equipped(PLAYER,item):
		gfx.message('You take off the %s.' % _name)
			
	gfx.message('You drop the %s.' % _name)
	life.drop_item(PLAYER,item)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def _pick_up_item_from_ground(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if not life.pick_up_item_from_ground(PLAYER,value):
		gfx.message('There\'s nowhere to put this!')
		
		return False
		
	gfx.message('You pick up a %s.' % value)
	
	_items = items.get_items_at(PLAYER['pos'])
	menus.delete_menu(ACTIVE_MENU['menu'])
	
	if _items:
		create_pick_up_item_menu(_items)
		return True

def create_pick_up_item_menu(items):
	_menu_items = []
	
	for item in items:
		_menu_items.append(menus.create_item('single',0,item['name'],icon=item['icon']))
	
	_i = menus.create_menu(title='Pick up',
		menu=_menu_items,
		padding=(1,1),
		position=(1,1),
		format_str='[$i] $k: $v',
		on_select=_pick_up_item_from_ground)
	
	menus.activate_menu(_i)

def return_to_inventory(entry):
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.activate_menu_by_name('Inventory')

LIGHTS.append({'x': 40,'y': 30,'brightness': 40.0})

life.initiate_life('Human')
_test = life.create_life('Human',name=['derp','yerp'],map=MAP)
life.add_action(_test,{'action': 'move', 'to': (50,0)},200)
PLAYER = life.create_life('Human',name=['derp','yerp'],map=MAP)

items.initiate_item('white_shirt')
items.initiate_item('sneakers')
items.initiate_item('leather_backpack')

_i1 = items.create_item('white t-shirt')
_i2 = items.create_item('sneakers')
_i3 = items.create_item('sneakers')
_i4 = items.create_item('sneakers',position=(10,10,2))
_i4 = items.create_item('white t-shirt',position=(10,10,2))

life.equip_item(PLAYER,life.add_item_to_inventory(PLAYER,_i1))
life.equip_item(PLAYER,life.add_item_to_inventory(PLAYER,_i2))
life.equip_item(PLAYER,life.add_item_to_inventory(PLAYER,_i3))

CURRENT_UPS = UPS

while RUNNING:
	get_input()
	handle_input()
	_played_moved = False

	while life.get_highest_action(PLAYER):
		life.tick_all_life()
		_played_moved = True
		
		if CURRENT_UPS:
			CURRENT_UPS-=1
		else:
			CURRENT_UPS = UPS
			break
	
	if not _played_moved:
		life.tick_all_life()
	
	gfx.start_of_frame()
	
	if CYTHON_ENABLED:
		render_map.render_map(MAP)
	else:
		maps.render_map(MAP)
	
	maps.render_lights()
	items.draw_items()
	move_camera()
	life.draw_life()
	life.draw_visual_inventory(PLAYER)
	menus.align_menus()
	menus.draw_menus()
	gfx.draw_bottom_ui()
	gfx.draw_console()
	gfx.end_of_frame_reactor3()
	gfx.end_of_frame()

maps.save_map(MAP)
