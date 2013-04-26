from globals import *
from libtcodpy import *

import graphics
import worldgen
import profiles
import menus

HEADER = ['Reactor 3',
	'- - -',
	'Return to Pripyat',
	'- - -',
	'']
HEADER.reverse()

MAIN_MENU_TEXT = ['s - World Select  ',
	'w - World Generation',
	'o - Options',
	'q - Quit   ']

WORLD_INFO_TEXT = ['placeholder']

[MAIN_MENU_TEXT.insert(0, line) for line in HEADER]
[WORLD_INFO_TEXT.insert(0, line) for line in HEADER]

MENU = [MAIN_MENU_TEXT]

def draw_main_menu():
	menus.draw_menus()
	graphics.end_of_frame()

def switch_to_main_menu():
	menus.delete_active_menu()
	
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Start', None))
	_menu_items.append(menus.create_item('single', 'Select World', None, enabled=profiles.get_worlds()))
	_menu_items.append(menus.create_item('single', 'World Generation', None))
	_menu_items.append(menus.create_item('single', 'Quit', None))
	
	_i = menus.create_menu(title='Reactor 3',
		menu=_menu_items,
		padding=(1,1),
		position=(MAP_WINDOW_SIZE[0],0),
		format_str='$k',
		on_select=main_menu_select,
		on_change=None)
	
	menus.activate_menu(_i)
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def switch_to_start_game():
	menus.delete_active_menu()
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Existing Character', None, enabled=False))
	_menu_items.append(menus.create_item('single', 'New Character', None))
	_menu_items.append(menus.create_item('single', 'New Character (Advanced)', None, enabled=False))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Scenario',
		menu=_menu_items,
		padding=(1,1),
		position=(MAP_WINDOW_SIZE[0],0),
		format_str='$k',
		on_select=start_menu_select,
		on_change=None)
	
	menus.activate_menu(_i)
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def switch_to_select_world():
	menus.delete_active_menu()
	_menu_items = []
	
	for world in profiles.get_worlds():
		_menu_items.append(menus.create_item('single', 'World %s' % world, None, world=world))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Scenario',
		menu=_menu_items,
		padding=(1,1),
		position=(MAP_WINDOW_SIZE[0],0),
		format_str='$k',
		on_select=world_select_select,
		on_change=None)
	
	menus.activate_menu(_i)
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def switch_to_spawn_point():
	menus.delete_active_menu()
	
	#TODO: List of camps
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Zone Entry Point', None))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Spawn Point',
		menu=_menu_items,
		padding=(1,1),
		position=(MAP_WINDOW_SIZE[0],0),
		format_str='$k',
		on_select=spawn_menu_select,
		on_change=None)
	
	menus.activate_menu(_i)
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def switch_to_world_gen():
	_menu_items = []
	_menu_items.append(menus.create_item('list', 'World Age', ['Day 0','1 Week', '2 Weeks', '3 Weeks']))
	_menu_items.append(menus.create_item('list', 'Life Density', ['Sparse', 'Medium', 'Heavy']))
	_menu_items.append(menus.create_item('list', 'Artifacts', ['Few', 'Normal', 'Many']))
	_menu_items.append(menus.create_item('list', 'Economy', ['Weak', 'Stable', 'Strong']))
	_menu_items.append(menus.create_item('spacer', '-', None))
	_menu_items.append(menus.create_item('single', 'Generate', None))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='World Generation',
		menu=_menu_items,
		padding=(1,1),
		position=(MAP_WINDOW_SIZE[0],0),
		on_select=worldgen_menu_select,
		on_change=refresh_screen)
	
	menus.activate_menu(_i)
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def refresh_screen(entry):
	#TODO: Broken. Menus should be handling this anyway
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def start_game():
	SETTINGS['running'] = 2
	menus.delete_active_menu()

def generate_world():
	_menu = MENUS[menus.get_menu_by_name('World Generation')]
	_settings = {}
	
	for entry in _menu['menu']:
		_settings[entry['key']] = entry['values'][entry['value']]
	
	if _settings['World Age'] == 'Day 0':
		_ticks = 100
	elif _settings['World Age'] == '1 Week':
		_ticks = 30000
	elif _settings['World Age'] == '2 Weeks':
		_ticks = 60000
	elif _settings['World Age'] == '3 Weeks':
		_ticks = 90000
	
	if _settings['Life Density'] == 'Sparse':
		_life = 4
	elif _settings['Life Density'] == 'Medium':
		_life = 8
	elif _settings['Life Density'] == 'Heavy':
		_life = 12
	
	worldgen.generate_world(WORLD_INFO['map'], life=_life, simulate_ticks=_ticks)

def main_menu_select(entry):
	key = entry['key']
	
	if key == 'Start':
		switch_to_start_game()
	elif key == 'Select World':
		switch_to_select_world()
	elif key == 'World Generation':
		switch_to_world_gen()
	elif key == 'Quit':
		SETTINGS['running'] = False

def start_menu_select(entry):
	key = entry['key']
	
	if key == 'New Character':
		switch_to_spawn_point()
	elif key == 'Back':
		switch_to_main_menu()

def world_select_select(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key.count('World'):
		print 'Load',entry['world']
	elif key == 'Back':
		switch_to_main_menu()

def spawn_menu_select(entry):
	key = entry['key']
	
	if key == 'Zone Entry Point':
		start_game()
	elif key == 'Back':
		switch_to_start_game()

def worldgen_menu_select(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Generate':
		generate_world()
	elif key == 'Back':
		switch_to_start_game()
