from globals import *
from libtcodpy import *

import graphics
import worldgen
import profiles
import numbers
import mapgen
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
FLOOD_POINTS = []

def draw_intro():
	_stime = time.time()
	_title_time = time.time()
	_warning_time = None
	_sub_line = 'Reactor 3'
	_warning_message = VERSION
	_sub_mod = 0
	_sub_time = 0
	_shadow = 50
	_burn = 8.0
	
	#Why did I base this on time.time()?
	while time.time()-_stime<=5:
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
			
			if 4.0>time.time()-_stime:
				_burn *= 1.005
			elif time.time()-_stime>=4.0:
				if _burn>255:
					_burn = 255
				
				_burn *= .99
			
			_text = INTRO
		
		_mod = int(round(255*numbers.clip(time.time()-_title_time, 0, 1)))
		
		console_set_default_foreground(0, Color(_mod, _mod, _mod))
		console_print(0, (WINDOW_SIZE[0]/2)-len(_text)/2, (WINDOW_SIZE[1]/2)-2, _text)
		
		if time.time()-_stime>=1:
			if not _warning_time:
				_warning_time = time.time()
			
			_mod = int(round(255*numbers.clip(time.time()-_warning_time, 0, 1)))
		
			console_set_default_foreground(0, Color(_mod/2, _mod/2, _mod/2))
			console_print(0, 0, WINDOW_SIZE[1]-1, _warning_message)
		
		_i = 0
		for c in _sub_line:
			if _sub_time:
				_delta = numbers.clip((time.time()-_sub_time)*6.0, 0, len(_sub_line)*2)
				_upper = numbers.clip(255-(abs(_i-_delta))*_shadow, 0, 255)
				#_sub_mod = int(round(_upper*numbers.clip((time.time()-_sub_time)*2, 0, 1)))
			
				#if _sub_mod < 1 and _i-_delta<0:
				#_sub_mod = numbers.clip(_sub_mod, 1, 255)
				_r = numbers.clip(numbers.clip(int(round(_burn)), 0, 255)-random.randint(0, 75), 0, 255)
				#else:
				#	_r = _sub_mod
			else:
				_r = _sub_mod
			
			console_set_default_foreground(0, Color(_r, _sub_mod, _sub_mod))
			console_print(0, ((WINDOW_SIZE[0]/2)-len(_sub_line)/2)+_i, (WINDOW_SIZE[1]/2), c)
			_i += 1
		
		console_flush()
	
	SETTINGS['running'] = 1

def clear(*args):
	console_rect(0,0,0,WINDOW_SIZE[0],WINDOW_SIZE[1],True,flag=BKGND_DEFAULT)
	_c = random.choice([tcod.sepia, tcod.brass, tcod.gray])
	
	for y in range(WINDOW_SIZE[1]):
		for x in range(WINDOW_SIZE[0]):
			if not time.time()%0.1:
				continue
			
			_mod = random.randint(0, 10)
			tcod.console_put_char_ex(0, x, y, chr(random.randint(0, 125)),
			                         tcod.Color(numbers.clip(_c.r+_mod, 0, 255),
			                                    numbers.clip(_c.g+_mod, 0, 255),
			                                    numbers.clip(_c.b+_mod, 0, 255)),
			                         tcod.Color(_c.r+_mod, _c.g+_mod, _c.b+_mod))
	
	console_flush()

def draw_message():
	console_set_default_foreground(0, tcod.white)
	_y = 25
	for line in MESSAGE:
		#graphics.blit_string(1, _y, line)
		console_print(0, 1, _y, line)
		_y += 1

def draw_main_menu():
	menus.align_menus()
	menus.draw_menus()
	draw_message()
	graphics.end_of_frame(draw_map=False)

def switch_to_main_menu():
	while MENUS:
		MENUS.pop(0)
	
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
		on_change=None,
		on_close=clear)
	
	menus.activate_menu(_i)
	clear()

def switch_to_start_game():
	while menus.delete_active_menu():
		continue
	
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Existing Character', None, enabled=SETTINGS['controlling']))
	_menu_items.append(menus.create_item('single', 'New Character', None))
	_menu_items.append(menus.create_item('single', 'New Character (Advanced)', None, enabled=False))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Scenario',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		format_str='$k',
		on_select=start_menu_select,
		on_change=None,
		on_close=clear)
	
	menus.activate_menu(_i)
	clear()

def switch_to_select_world():
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
		on_change=None,
		on_close=clear)
	
	menus.activate_menu(_i)
	clear()

def switch_to_spawn_point():
	#TODO: List of camps
	_menu_items = []
	_menu_items.append(menus.create_item('single', 'Random', 'Randomized story'))
	_menu_items.append(menus.create_item('single', 'Zone Entry Point', 'Near Rookie camp', enabled=False))
	_menu_items.append(menus.create_item('single', 'Chase', 'You are being trailed!', enabled=False))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='Spawn Point',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		format_str='$k ($v)',
		on_select=spawn_menu_select,
		on_change=None,
		on_close=clear)
	
	menus.activate_menu(_i)
	clear()

def switch_to_world_gen():
	_maps = ['Generate Map']
	_maps.extend(profiles.get_maps())
	
	_menu_items = []
	_menu_items.append(menus.create_item('list', 'Map', _maps))
	_menu_items.append(menus.create_item('list', 'World Age', ['Day 0','1 Week', '2 Weeks', '3 Weeks', '4 Weeks', '5 Weeks'], enabled=False))
	_menu_items.append(menus.create_item('list', 'Dynamic Spawns', ['None', 'Sparse', 'Medium', 'Heavy']))
	_menu_items.append(menus.create_item('list', 'Wildlife Density', ['None', 'Sparse', 'Medium', 'Heavy'], enabled=False))
	_menu_items.append(menus.create_item('list', 'Artifacts', ['Few', 'Normal', 'Many'], enabled=False))
	_menu_items.append(menus.create_item('list', 'Economy', ['Weak', 'Stable', 'Strong'], enabled=False))
	_menu_items.append(menus.create_item('spacer', '-', None))
	_menu_items.append(menus.create_item('single', 'Generate', None))
	_menu_items.append(menus.create_item('single', 'Back', None))
	
	_i = menus.create_menu(title='World Generation',
		menu=_menu_items,
		padding=(1,1),
		position=(0,0),
		on_select=worldgen_menu_select,
		on_close=clear)
	
	menus.activate_menu(_i)
	clear()

def start_game():
	SETTINGS['running'] = 2
	
	graphics.prepare_map_views()
	
	while MENUS:
		menus.delete_active_menu()
	
	graphics.glitch_text(WORLD_INFO['title'])

def generate_world(combat_test=False):
	_menu = MENUS[menus.get_menu_by_name('World Generation')]
	_settings = {}
	
	for entry in _menu['menu']:
		_settings[entry['key']] = entry['values'][entry['value']]
	
	if _settings['Map'] == 'Generate Map':
		_settings['Map'] = mapgen.generate_map(size=(250, 650, 10),
		                                       towns=1,
		                                       factories=0,
		                                       outposts=2,
		                                       forests=1)['name']
	
	if _settings['World Age'] == 'Day 0':
		_ticks = 10
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
		dynamic_spawns=_settings['Dynamic Spawns'],
		wildlife_spawns=_settings['Wildlife Density'],
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
	
	if key in ['Zone Entry Point', 'Random']:
		worldgen.create_player()
		start_game()
	elif key == 'Back':
		switch_to_start_game()

def worldgen_menu_select(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Generate':
		graphics.title('Setting up world...')
		generate_world()
		switch_to_main_menu()
	elif key == 'Combat Test':
		graphics.title('Creating combat test...')
		generate_world(combat_test=True)
		switch_to_main_menu()
	elif key == 'Back':
		switch_to_main_menu()
