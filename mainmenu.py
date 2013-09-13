from globals import *
from libtcodpy import *

import graphics
import worldgen
import profiles
import numbers
import menus
import maps

import random
import time

INTRO = 'flagsdev presents'
MESSAGE = ['Reactor 3 is still a prototype',
	'You may experience slow performance and crashes',
	'',
	'Send any bug reports to:',
	'https://github.com/flags/Reactor-3/issues',
     '',
     'Version: %s' % VERSION]

def draw_intro():
	_stime = time.time()
	_title_time = time.time()
	_sub_line = 'Reactor 3'
	_sub_mod = 0
	_sub_time = 0
	_shadow = 50
	_burn = 1
	
	while time.time()-_stime<=7:
		_text = INTRO
		
		if time.time()-_stime<=1:
			_text = list(_text)
			random.shuffle(_text)
			_text = ''.join(_text)
		else:
			if not _sub_time:
				_sub_time = time.time()
			elif time.time()-_stime>=3.2:
				#_shadow *= 1.05
				#_sub_time += .042
				_title_time += .044
			
			if 6>time.time()-_stime>=2.0:
				_burn *= 1.035
			elif time.time()-_stime>=6:
				_burn *= .88
			
			_text = INTRO
		
		_mod = int(round(255*numbers.clip(time.time()-_title_time, 0, 1)))
		
		console_set_default_foreground(0, Color(_mod, _mod, _mod))
		console_print(0, (WINDOW_SIZE[0]/2)-len(_text)/2, (WINDOW_SIZE[1]/2)-2, _text)
		
		_i = 0
		for c in _sub_line:
			if _sub_time:
				_delta = numbers.clip((time.time()-_sub_time)*6.0, 0, len(_sub_line)*2)
				_upper = numbers.clip(255-(abs(_i-_delta))*_shadow, 0, 255)
				_sub_mod = int(round(_upper*numbers.clip((time.time()-_sub_time)*2, 0, 1)))
			
				if _sub_mod < 1 and _i-_delta<0:
					_sub_mod = numbers.clip(_sub_mod, 1, 255)
					_r = numbers.clip(numbers.clip(int(round(_sub_mod*_burn)), 0, 255)-random.randint(0, 75), 0, 255)
				else:
					_r = _sub_mod
			else:
				_r = _sub_mod
			
			console_set_default_foreground(0, Color(_r, _sub_mod, _sub_mod))
			console_print(0, ((WINDOW_SIZE[0]/2)-len(_sub_line)/2)+_i, (WINDOW_SIZE[1]/2), c)
			_i += 1
		
		console_flush()
	
	SETTINGS['running'] = 1

def clear(entry=None):
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)
	console_flush()

def draw_message():
	_y = 25
	for line in MESSAGE:
		graphics.blit_string(1, _y, line)
		_y += 1
	
	graphics.start_of_frame()

def draw_main_menu():
	menus.draw_menus()
	draw_message()
	graphics.end_of_frame()

def switch_to_main_menu():
	menus.delete_active_menu()
	
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Start', None, enabled=WORLD_INFO['id']))
	_menu_items.append(menus.create_item('single', 'Select World', None, enabled=profiles.get_worlds()))
	_menu_items.append(menus.create_item('single', 'World Generation', None))
	_menu_items.append(menus.create_item('single', 'Quit', None))
	
	_i = menus.create_menu(title='Reactor 3',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		format_str='$k',
		on_select=main_menu_select,
		on_change=None)
	
	menus.activate_menu(_i)
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)

def switch_to_start_game():
	menus.delete_active_menu()
	
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Existing Character', None, enabled=LIFE[SETTINGS['controlling']]))
	_menu_items.append(menus.create_item('single', 'New Character', None))
	_menu_items.append(menus.create_item('single', 'New Character (Advanced)', None, enabled=False))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Scenario',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		format_str='$k',
		on_select=start_menu_select,
		on_change=None)
	
	menus.activate_menu(_i)
	clear()

def switch_to_select_world():
	menus.delete_active_menu()
	_menu_items = []
	
	for world in profiles.get_worlds():
		_menu_items.append(menus.create_item('single', 'World %s' % world, None, world=world, enabled=(not world == WORLD_INFO['id'])))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Select World',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		format_str='$k',
		on_select=world_select_select,
		on_change=None)
	
	menus.activate_menu(_i)
	clear()

def switch_to_spawn_point():
	menus.delete_active_menu()
	
	#TODO: List of camps
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Zone Entry Point', 'Near Rookie camp'))
	_menu_items.append(menus.create_item('single', 'Chase', 'You are being trailed!'))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Spawn Point',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		format_str='$k ($v)',
		on_select=spawn_menu_select,
		on_change=None)
	
	menus.activate_menu(_i)
	clear()

def switch_to_world_gen():
	_menu_items = []
	_menu_items.append(menus.create_item('list', 'Map', profiles.get_maps()))
	_menu_items.append(menus.create_item('list', 'World Age', ['Day 0','1 Week', '2 Weeks', '3 Weeks', '4 Weeks', '5 Weeks']))
	_menu_items.append(menus.create_item('list', 'Life Density', ['Sparse', 'Medium', 'Heavy', 'None']))
	_menu_items.append(menus.create_item('list', 'Wildlife Density', ['Sparse', 'Medium', 'Heavy', 'None']))
	_menu_items.append(menus.create_item('list', 'Artifacts', ['Few', 'Normal', 'Many']))
	_menu_items.append(menus.create_item('list', 'Economy', ['Weak', 'Stable', 'Strong']))
	_menu_items.append(menus.create_item('spacer', '-', None))
	_menu_items.append(menus.create_item('single', 'Generate', None))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='World Generation',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		on_select=worldgen_menu_select)
	
	menus.activate_menu(_i)
	clear()

def start_game():
	SETTINGS['running'] = 2
	menus.delete_active_menu()
	menus.delete_active_menu()

def generate_world():
	_menu = MENUS[menus.get_menu_by_name('World Generation')]
	_settings = {}
	
	for entry in _menu['menu']:
		_settings[entry['key']] = entry['values'][entry['value']]
	
	if _settings['World Age'] == 'Day 0':
		_ticks = 100
	elif _settings['World Age'] == '1 Week':
		_ticks = 1000#30000
	elif _settings['World Age'] == '2 Weeks':
		_ticks = 2000
	elif _settings['World Age'] == '3 Weeks':
		_ticks = 3000
	elif _settings['World Age'] == '4 Weeks':
		_ticks = 4000
	elif _settings['World Age'] == '5 Weeks':
		_ticks = 5000
	
	maps.load_map(_settings['Map'])
	
	worldgen.generate_world(WORLD_INFO['map'],
		life_density=_settings['Life Density'],
		wildlife_density=_settings['Wildlife Density'],
		simulate_ticks=_ticks,
	     save=True,
		thread=True)

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
		sys.exit(0)

def start_menu_select(entry):
	key = entry['key']
	
	if key == 'New Character':
		switch_to_spawn_point()
	elif key == 'Existing Character':
		start_game()
	elif key == 'Back':
		switch_to_main_menu()

def world_select_select(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key.count('World'):
		worldgen.load_world(entry['world'])

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
		graphics.title('Setting up world...')
		generate_world()
	elif key == 'Back':
		switch_to_main_menu()
