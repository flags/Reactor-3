from globals import *
from libtcodpy import *

import graphics
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
	_menu_items.append(menus.create_item('list','Blit z-level below',['Off','On']))
	
	_i = menus.create_menu(title='Reactor 3',
		menu=_menu_items,
		padding=(1,1),
		position=(MAP_WINDOW_SIZE[0],0),
		on_select=None,
		on_change=None)
	
	menus.activate_menu(_i)
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def start_game():
	SETTINGS['running'] = 2
	menus.delete_active_menu()

def main_menu_select(entry):
	key = entry['key']
	
	if key == 'Start':
		switch_to_start_game()
	elif key == 'Quit':
		SETTINGS['running'] = False

def start_menu_select(entry):
	key = entry['key']
	
	if key == 'New Character':
		switch_to_spawn_point()
	elif key == 'Back':
		switch_to_main_menu()

def spawn_menu_select(entry):
	key = entry['key']
	
	if key == 'Zone Entry Point':
		start_game()
	elif key == 'Back':
		switch_to_start_game()
