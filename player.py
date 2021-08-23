from globals import *
from alife import *
from overwatch import events

import libtcodpy as tcod
import graphics as gfx

import crafting
import worldgen
import bad_numbers
import weapons
import dialog
import timers
import inputs
import melee
import debug
import zones
import logic
import menus
import items
import time
import life
import maps

import logging

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	if gfx.window_is_closed():
		SETTINGS['running'] = False
		
		return True
	
	if INPUT['\x1b'] or INPUT['q']:
		if ACTIVE_MENU['menu'] >= 0:
			menus.delete_menu(ACTIVE_MENU['menu'], abort=True)
		elif LIFE[SETTINGS['controlling']]['targeting']:
			LIFE[SETTINGS['controlling']]['targeting'] = None
			LIFE[SETTINGS['controlling']]['throwing'] = None
			LIFE[SETTINGS['controlling']]['firing'] = None
			SELECTED_TILES[0] = []
		elif LIFE[SETTINGS['controlling']]['actions']:
			life.clear_actions(LIFE[SETTINGS['controlling']])
			life.stop(LIFE[SETTINGS['controlling']])
			
			if LIFE[SETTINGS['controlling']]['actions']:
				LIFE[SETTINGS['controlling']]['actions'] = []
		elif INPUT['\x1b']:
			SETTINGS['running'] = False
		
		gfx.refresh_view('map')
	
	if INPUT['\t']:
		if not SETTINGS['controlling'] or not LIFE[SETTINGS['controlling']]['group']:
			return False
		
		_menu_items = [menus.create_item('single', 'Attack', 'Focus attack on target.')]
		_menu_items.append(menus.create_item('single', 'Health', 'Check health of...'))
		_menu_items.append(menus.create_item('single', 'Location', 'Get location of...'))
	
		_menu = menus.create_menu(title='Command',
			menu=_menu_items,
			padding=(1,1),
			position=(1,1),
			format_str='$k: $v',
			on_select=send_command)
		
		menus.activate_menu(_menu)
	
	if INPUT['-']:
		if SETTINGS['draw console']:
			SETTINGS['draw console'] = False
		else:
			SETTINGS['draw console'] = True
	
	if SETTINGS['draw console']:
		return

	if INPUT['up'] or (SETTINGS['controlling'] and INPUT['8']):
		if not ACTIVE_MENU['menu'] == -1:
			menus.move_up(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		elif LIFE[SETTINGS['controlling']]['targeting']:
			LIFE[SETTINGS['controlling']]['targeting'][1]-=1
		elif life.has_dialog(LIFE[SETTINGS['controlling']]):
			_dialog = dialog.get_dialog(life.has_dialog(LIFE[SETTINGS['controlling']]))
			
			if _dialog['cursor_index'] > 0:
				_dialog['cursor_index'] -= 1
		elif LIFE[SETTINGS['controlling']]['pos'][1]>0 and not LIFE[SETTINGS['controlling']]['dead']:
			life.clear_actions(LIFE[SETTINGS['controlling']])
			life.add_action(LIFE[SETTINGS['controlling']],{'action': 'move', 'to': (LIFE[SETTINGS['controlling']]['pos'][0], LIFE[SETTINGS['controlling']]['pos'][1]-1, LIFE[SETTINGS['controlling']]['pos'][2])},200)

	if INPUT['down'] or (SETTINGS['controlling'] and INPUT['2']):
		if not ACTIVE_MENU['menu'] == -1:
			menus.move_down(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		elif LIFE[SETTINGS['controlling']]['targeting']:
			LIFE[SETTINGS['controlling']]['targeting'][1]+=1
		elif life.has_dialog(LIFE[SETTINGS['controlling']]):
			_dialog = dialog.get_dialog(life.has_dialog(LIFE[SETTINGS['controlling']]))
			
			if _dialog['cursor_index'] < _dialog['max_cursor_index']-1:
				_dialog['cursor_index'] += 1
		elif LIFE[SETTINGS['controlling']]['pos'][1]<MAP_SIZE[1]-1 and not LIFE[SETTINGS['controlling']]['dead']:
			life.clear_actions(LIFE[SETTINGS['controlling']])
			life.add_action(LIFE[SETTINGS['controlling']],{'action': 'move', 'to': (LIFE[SETTINGS['controlling']]['pos'][0],LIFE[SETTINGS['controlling']]['pos'][1]+1, LIFE[SETTINGS['controlling']]['pos'][2])},200)

	if INPUT['right'] or (SETTINGS['controlling'] and INPUT['6']):
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		elif LIFE[SETTINGS['controlling']]['targeting']:
			LIFE[SETTINGS['controlling']]['targeting'][0]+=1
		elif LIFE[SETTINGS['controlling']]['pos'][0]<MAP_SIZE[0]-1 and not LIFE[SETTINGS['controlling']]['dead']:
			life.clear_actions(LIFE[SETTINGS['controlling']])
			life.add_action(LIFE[SETTINGS['controlling']],{'action': 'move', 'to': (LIFE[SETTINGS['controlling']]['pos'][0]+1,LIFE[SETTINGS['controlling']]['pos'][1], LIFE[SETTINGS['controlling']]['pos'][2])},200)

	if INPUT['left'] or (SETTINGS['controlling'] and INPUT['4']):
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		elif LIFE[SETTINGS['controlling']]['targeting']:
			LIFE[SETTINGS['controlling']]['targeting'][0]-=1
		elif LIFE[SETTINGS['controlling']]['pos'][0]>0 and not LIFE[SETTINGS['controlling']]['dead']:
			life.clear_actions(LIFE[SETTINGS['controlling']])
			life.add_action(LIFE[SETTINGS['controlling']],{'action': 'move', 'to': (LIFE[SETTINGS['controlling']]['pos'][0]-1,LIFE[SETTINGS['controlling']]['pos'][1], LIFE[SETTINGS['controlling']]['pos'][2])},200)
	
	if INPUT['\r']:
		if ACTIVE_MENU['menu'] > -1:
			menus.item_selected(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
			return False
			
		_dialog = life.has_dialog(LIFE[SETTINGS['controlling']])
		if SETTINGS['controlling'] and _dialog:
			dialog.select_choice(_dialog)
			
			#if '_drawn' in _dialog:
			#	del _dialog['_drawn']
			
			#dialog.give_menu_response(LIFE[SETTINGS['controlling']], _dialog)
			return False
	
	if not SETTINGS['controlling']:
		return False
	
	if INPUT['.'] or (SETTINGS['controlling'] and INPUT['5']):
		_skip = False
		
		for event in EVENTS:
			if not event['delay']:
				_skip = True
				break
				
		if not _skip:
			life.add_action(LIFE[SETTINGS['controlling']], {'action': 'rest'}, 200)
		else:
			logic.show_next_event()
	
	if INPUT[' ']:
		if SETTINGS['paused']:
			SETTINGS['paused'] = False
			gfx.refresh_view('map')
		else:
			SETTINGS['paused'] = True
			gfx.refresh_view('map')
	
	if INPUT['?']:
		#gfx.screenshot()
		if SETTINGS['recording']:
			SETTINGS['recording'] = False
			logging.info('Stopped recording')
		else:
			SETTINGS['recording'] = True
			logging.info('Recording')
	
	if INPUT['P']:
		if SETTINGS['paused']:
			SETTINGS['paused'] = False
		else:
			SETTINGS['paused'] = True
	
	if INPUT['a']:
		if menus.get_menu_by_name('Activate')>-1:
			menus.delete_menu(menus.get_menu_by_name('Activate'))
			return False
		
		_items = []
		for entry in life.get_fancy_inventory_menu_items(LIFE[SETTINGS['controlling']], show_containers=False, check_hands=True):
			if not 'id' in entry:
				continue
			
			if 'ON_ACTIVATE' in ITEMS[entry['id']]['flags']:
				_items.append(entry)
		
		_nearby_items = []
		for item_uid in LIFE[SETTINGS['controlling']]['seen_items']:
			_item = ITEMS[item_uid]
			
			if not 'ON_ACTIVATE' in ITEMS[item_uid]['flags']:
				continue
			
			if bad_numbers.distance(LIFE[SETTINGS['controlling']]['pos'], ITEMS[item_uid]['pos'])>1:
				continue
			
			_nearby_items.append(menus.create_item('single', _item['name'], None, icon=_item['icon'], id=item_uid))
		
		if _nearby_items:
			_items.append(menus.create_item('title', 'Nearby', None))
			_items.extend(_nearby_items)
		
		if not _items:
			gfx.message('You have no items to activate.')
			return False
		
		_i = menus.create_menu(title='Activate',
			menu=_items,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=lambda entry: life.activate_item(LIFE[SETTINGS['controlling']], entry['id']),
		     close_on_select=True)
		
		menus.activate_menu(_i)

	if INPUT['A']:
		if menus.get_menu_by_name('Eat')>-1:
			menus.delete_menu(menus.get_menu_by_name('Eat'))
			return False
		
		_food = []
		for _item in life.get_all_inventory_items(LIFE[SETTINGS['controlling']], matches=[{'type': 'food'}, {'type': 'drink'}, {'type': 'medicine'}]):
			_food.append(menus.create_item('single',
				items.get_name(_item),
				None,
				icon=_item['icon'],
				id=_item['uid']))
		
		if not _food:
			gfx.message('You have nothing to eat.')
			return False
		
		_i = menus.create_menu(title='Eat',
			menu=_food,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k',
			on_select=inventory_eat)
		
		menus.activate_menu(_i)

	if INPUT['i']:
		if menus.get_menu_by_name('Inventory')>-1:
			menus.delete_menu(menus.get_menu_by_name('Inventory'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(LIFE[SETTINGS['following']],check_hands=True)
		
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
		
		_inventory = life.get_fancy_inventory_menu_items(LIFE[SETTINGS['controlling']],show_equipped=False,check_hands=False)
		
		if not _inventory:
			gfx.message('You have no items to equip.')
			
			return False
		
		_i = menus.create_menu(title='Equip',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k',
			on_select=inventory_select,
		    action='Equip')
		
		menus.activate_menu(_i)
	
	if INPUT['E']:
		if menus.get_menu_by_name('Unequip')>-1:
			menus.delete_menu(menus.get_menu_by_name('Equip'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(LIFE[SETTINGS['controlling']],show_equipped=True,check_hands=True,show_containers=False)
		
		if not _inventory:
			gfx.message('You have no items to unequip.')
			return False
		
		_i = menus.create_menu(title='Unequip',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k',
			on_select=inventory_select,
		    action='Unequip')
		
		menus.activate_menu(_i)
	
	if INPUT['c']:
		life.crouch(LIFE[SETTINGS['controlling']])
	
	if INPUT['C']:
		life.stand(LIFE[SETTINGS['controlling']])
	
	if INPUT['d']:
		if menus.get_menu_by_name('Drop')>-1:
			menus.delete_menu(menus.get_menu_by_name('Drop'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(LIFE[SETTINGS['controlling']], show_containers=True, check_hands=True)
		
		if not _inventory:
			gfx.message('You have no items to drop.')
			return False
		
		_i = menus.create_menu(title='Drop',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_select,
		    action='Drop')
		
		menus.activate_menu(_i)
	
	if INPUT['t']:
		if not menus.get_menu_by_name('Arm')==-1:
			return False
		
		if menus.get_menu_by_name('Throw')>-1 and menus.get_menu_by_name('Arm')==-1:
			menus.delete_menu(menus.get_menu_by_name('Throw'))
			return False
		
		if LIFE[SETTINGS['controlling']]['targeting']:
			life.throw_item(LIFE[SETTINGS['controlling']], LIFE[SETTINGS['controlling']]['throwing'], LIFE[SETTINGS['controlling']]['targeting'])
			LIFE[SETTINGS['controlling']]['targeting'] = None
			SELECTED_TILES[0] = []
			return True
		
		_throwable = life.get_fancy_inventory_menu_items(LIFE[SETTINGS['controlling']], show_equipped=True, check_hands=True)
		
		if not _throwable:
			return False
		
		_i = menus.create_menu(title='Throw',
			menu=_throwable,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_select,
		    action='Throw')
		
		menus.activate_menu(_i)
	
	if INPUT['T']:
		if not ACTIVE_MENU['menu'] == -1:
			return False
		
		create_tracking_menu()
	
	if INPUT['v']:
		if menus.get_menu_by_name('Talk')>-1:
			menus.delete_menu(menus.get_menu_by_name('Talk'))
			return False
		
		if not LIFE[SETTINGS['controlling']]['targeting']:
			_menu_items = menus.create_target_list()
	
			if not len(_menu_items)>1:
				gfx.message('There\'s nobody to talk to.')
				return False
		
			_i = menus.create_menu(title='Talk to...',
				menu=_menu_items,
				padding=(1,1),
				position=(1,1),
				format_str='$k',
				on_select=create_dialog,
				on_close=exit_target,
				on_move=target_view)
		
			menus.activate_menu(_i)
			return True
		else:
			_target = None
			for entry in [LIFE[i] for i in LIFE]:
				if entry['pos'] == LIFE[SETTINGS['controlling']]['targeting']:
					_target = entry
					break
			
			if not _target:
				gfx.message('There\'s nobody standing here!')
				return False
	
	if INPUT['V']:
		if menus.get_menu_by_name('Radio')>-1:
			menus.delete_menu(menus.get_menu_by_name('Radio'))
		else:
			return create_radio_menu()

	if INPUT['m']:
		if not ACTIVE_MENU['menu'] == -1:
			return False
		
		_player = LIFE[SETTINGS['controlling']]
		_menu_items = []
		
		for mission in list(_player['missions'].values()):
			if not mission['tasks']:
				continue
			
			_menu_items.append(menus.create_item('title', mission['name'], None))
			
			for task_id in mission['tasks']:
				_task = mission['tasks'][task_id]
				
				if _task['completed']:
					_completed = 'x'
				else:
					_completed = ' '
				
				_menu_items.append(menus.create_item('single', _completed, _task['description'], enabled=_completed == ' '))
		
		if not _menu_items:
			gfx.message('You have no missions.')
			
			return False
		
		_i = menus.create_menu(title='Missions',
		                       menu=_menu_items,
		                       padding=(1,1),
		                       position=(1,1),
		                       format_str='[$k] $v')
		
		menus.activate_menu(_i)

	if INPUT['M']:
		if menus.get_menu_by_name('Fight')>-1:
			return False
		
		_menu_items = menus.create_target_list()

		if not _menu_items:
			gfx.message('You have nothing to aim at!')
			return False
	
		_i = menus.create_menu(title='Fight',
	          menu=_menu_items,
	          padding=(1,1),
	          position=(1,1),
	          format_str='$k',
	          on_select=handle_advanced_movement,
	          on_close=exit_target,
	          on_move=target_view)
		
		menus.activate_menu(_i)

	if INPUT['f']:
		if menus.get_menu_by_name('Select Limb')>-1:
			return False
		
		if menus.get_menu_by_name('Aim at...')>-1:
			return False
			
		if menus.get_menu_by_name('Fire')>-1:
			menus.delete_menu(menus.get_menu_by_name('Fire'))
			return False
		
		if LIFE[SETTINGS['controlling']]['targeting']:
			if menus.get_menu_by_name('Select Target')>-1:
				return False
			
			_alife_menu = []
			for _life in life.get_all_life_at_position(life, LIFE[SETTINGS['controlling']]['targeting']):
				_alife = LIFE[_life]
				
				_alife_menu.append(menus.create_item('single',
					'%s' % ' '.join(_alife['name']),
					'Nearby',
					target=_alife))
			
			if len(_alife_menu)>=2:
				_i = menus.create_menu(title='Select Target',
					menu=_alife_menu,
					padding=(1,1),
					position=(1,1),
					format_str='$k: $v',
					on_select=inventory_fire_select_limb)
				
				menus.activate_menu(_i)
			elif _alife_menu:
				inventory_fire_select_limb(_alife_menu[0], no_delete=True)
			
			return True
		
		_weapons = []
		for hand in LIFE[SETTINGS['controlling']]['hands']:
			_limb = life.get_limb(LIFE[SETTINGS['controlling']], hand)
			
			if not _limb['holding']:
				continue
			
			_item = life.get_inventory_item(LIFE[SETTINGS['controlling']],_limb['holding'][0])
			
			if _item['type'] == 'gun':
				_weapons.append(menus.create_item('single',
					_item['name'],
					'(Range: temp)',
					icon=_item['icon'],
					id=_item['uid']))
		
		if not _weapons:
			gfx.message('You have nothing to shoot!')
			return False
		
		_i = menus.create_menu(title='Fire',
			menu=_weapons,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_fire)
		
		#LIFE[SETTINGS['controlling']]['shoot_timer'] = LIFE[SETTINGS['controlling']]['shoot_timer_max']
		menus.activate_menu(_i)
	
	if INPUT['F']:
		if menus.get_menu_by_name('Fire Rate')>-1:
			return False
		
		_weapons = life.get_held_items(LIFE[SETTINGS['controlling']], matches=[{'type': 'gun'}])
		
		if not _weapons:
			gfx.message('You aren\'t holding any weapons.')
			return False
		
		_menu = []
		for _item in _weapons:
			_weapon = ITEMS[_item]
			_menu.append(menus.create_item('single',
			                                  _weapon['name'],
			                                  weapons.get_fire_mode(_weapon),
			                                  icon=_weapon['icon'],
			                                  item=_weapon['uid']))
		
		_i = menus.create_menu(title='Fire Rate',
			menu=_menu,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_change_fire_rate)
		
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
		
		for weapon in life.get_all_inventory_items(LIFE[SETTINGS['following']],matches=[{'type': 'gun'}]):
			_feed_uid = weapons.get_feed(weapon)
			
			if _feed_uid:
				_feed = items.get_item_from_uid(_feed_uid)
				
				_loaded_weapons.append(menus.create_item('single',
					weapon['name'],
					'%s/%s' % (len(_feed['rounds']),_feed['maxrounds']),
					icon=weapon['icon'],
					id=weapon['uid']))
			else:
				_unloaded_weapons.append(menus.create_item('single',
					weapon['name'],
					'Empty',
					icon=weapon['icon'],
					id=weapon['uid']))
		
		for ammo in life.get_all_inventory_items(LIFE[SETTINGS['following']],matches=[{'type': 'magazine'},{'type': 'clip'}]):
			#TODO: Make `parent` an actual key.
			if 'parent' in ammo:
				continue
			
			if ammo['rounds']:
				_non_empty_ammo.append(menus.create_item('single',
					ammo['name'],
					'%s/%s' % (len(ammo['rounds']),ammo['maxrounds']),
					icon=ammo['icon'],
					id=ammo['uid']))
			else:
				_empty_ammo.append(menus.create_item('single',
					ammo['name'],
					'%s/%s' % (len(ammo['rounds']),ammo['maxrounds']),
					icon=ammo['icon'],
					id=ammo['uid']))
			
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
	
	if INPUT['s']:
		if LIFE[SETTINGS['controlling']]['strafing']:
			LIFE[SETTINGS['controlling']]['strafing'] = False
			print('Not strafing')
		else:
			LIFE[SETTINGS['controlling']]['strafing'] = True
			print('Strafing')
	
	if INPUT['S']:
		#if not LIFE[SETTINGS['controlling']]['encounters']:
		#	return False
		
		#SETTINGS['following'] = LIFE[SETTINGS['controlling']]['id']
		#_target = LIFE[SETTINGS['controlling']]['encounters'].pop(0)['target']
		#LIFE[SETTINGS['controlling']]['shoot_timer'] = 0
		
		#speech.communicate(LIFE[SETTINGS['controlling']], 'surrender', matches=[{'id': _target['id']}])
		
		#logging.debug('** SURRENDERING **')
		if menus.get_menu_by_name('Stats')>-1:
			menus.delete_menu(menus.get_menu_by_name('Stats'))
			return False
		
		_stats = []
		_stats.append(menus.create_item('title', 'Stats', None))
		_stats.append(menus.create_item('spacer', '=', None))
		
		for key in LIFE[SETTINGS['controlling']]['stats']:
			if key == 'description':
				continue
			
			_stats.append(menus.create_item('single', key.title(), LIFE[SETTINGS['controlling']]['stats'][key]))
		
		_i = menus.create_menu(title='Options',
			menu=_stats,
			padding=(1,1),
			position=(1,1),
			format_str='$k: $v')
		
		menus.activate_menu(_i)
	
	if INPUT['j']:
		if LIFE[SETTINGS['controlling']]['job']:
			create_tasks_menu()
		else:
			create_jobs_menu()
		#for key in LIFE[SETTINGS['controlling']]['job']:
		#	if key == 'description':
		#		continue
		#	
		#	_stats.append(menus.create_item('single', key.title(), LIFE[SETTINGS['controlling']]['stats'][key]))
	
	if INPUT['w']:
		if menus.get_menu_by_name('Wounds')>-1:
			menus.delete_menu(menus.get_menu_by_name('Wounds'))
		else:
			create_wound_menu(SETTINGS['controlling'])
	
	if INPUT['W']:
		if menus.get_menu_by_name('Heal')>-1:
			menus.delete_menu(menus.get_menu_by_name('Heal'))
			return False
		
		_pos = LIFE[SETTINGS['controlling']]['pos']
		_items = []
			
		#Sue me.
		for life_id in LIFE[SETTINGS['controlling']]['seen']:
			if bad_numbers.distance(LIFE[SETTINGS['controlling']]['pos'], LIFE[life_id]['pos'])>1:
				continue
			
			_items.append(menus.create_item('single', ' '.join(LIFE[life_id]['name']), None, target=life_id))
		
		if not _items:
			gfx.message('There\'s nobody to heal nearby.')
			
			return False
		
		_i = menus.create_menu(title='Heal',
			menu=_items,
			padding=(1,1),
			position=(1,1),
			format_str='$k',
			on_select=create_target_wound_menu)
		
		menus.activate_menu(_i)
	
	if INPUT['O']:
		if menus.get_menu_by_name('Debug (Developer)')>-1:
			menus.delete_menu(menus.get_menu_by_name('Debug (Developer)'))
			return False
		
		_online_alife = len([l['id'] for l in list(LIFE.values()) if l['online'] and not l['dead'] and l['think_rate_max']<30])
		_online_alife_in_passive = len([l['id'] for l in list(LIFE.values()) if l['online'] and not l['dead'] and l['think_rate_max']>=30])
		_offline_alife = len([l['id'] for l in list(LIFE.values()) if not l['online'] and not l['dead']])
		
		_options = []
		_options.append(menus.create_item('title', 'Testing', None))
		_options.append(menus.create_item('list', 'Show camp ownership', str(len(WORLD_INFO['camps']))))
		_options.append(menus.create_item('list', 'Drop cache', 'Create cache drop'))
		_options.append(menus.create_item('list', 'Show visible chunks', ['off', 'on']))
		_options.append(menus.create_item('title', 'Map Operations', None))
		_options.append(menus.create_item('single', 'Save', 'Offload game to disk'))
		_options.append(menus.create_item('single', 'Load', 'Load game from disk'))
		_options.append(menus.create_item('single', 'Reload map', 'Reloads map from disk'))
		_options.append(menus.create_item('single', 'Update chunk map', 'Generates chunk map'))
		_options.append(menus.create_item('title', 'World Info', None))
		_options.append(menus.create_item('single', 'ALife (%s)' % len(LIFE), 'Online: %s (%s), Offline: %s' % (_online_alife, _online_alife_in_passive, _offline_alife)))
		_options.append(menus.create_item('single', 'ALife memories', sum([len(l['memory']) for l in list(LIFE.values()) if not l['dead']])))
		_options.append(menus.create_item('single', 'Groups', len(WORLD_INFO['groups'])))
		_options.append(menus.create_item('single', 'Seed', WORLD_INFO['seed']))
		
		_i = menus.create_menu(title='Debug (Developer)',
			menu=_options,
			padding=(1,1),
			position=(1,1),
			format_str='$k: $v',
			on_select=handle_options_menu,
		     on_change=handle_options_menu_change)
		
		menus.activate_menu(_i)
	
	if INPUT['z']:
		life.pass_out(LIFE[SETTINGS['controlling']], length=500)
	
	if INPUT['Z']:
		life.crawl(LIFE[SETTINGS['controlling']])
	
	if INPUT[',']:
		_items = items.get_items_at(LIFE[SETTINGS['controlling']]['pos'], check_bodies=True)
		
		if not _items:
			gfx.message('There is nothing here to pick up.')
			return False
		
		if menus.get_menu_by_name('Pick up')>-1:
			menus.delete_menu(menus.get_menu_by_name('Pick up'))
			return False
		
		create_pick_up_item_menu(_items)
	
	if INPUT['o']:
		_pos = LIFE[SETTINGS['controlling']]['pos']
		_items = []
		
		for pos in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1), (0, 0)]:
			__pos = (_pos[0]+pos[0], _pos[1]+pos[1], _pos[2])
			_items.extend(items.get_items_at(__pos))
			
		#Sue me again.
		for life_id in LIFE[SETTINGS['controlling']]['seen']:
			if bad_numbers.distance(LIFE[SETTINGS['controlling']]['pos'], LIFE[life_id]['pos'])>1:
				continue
			
			for item_uid in life.get_all_equipped_items(LIFE[life_id]):
				if 'capacity' in ITEMS[item_uid]:
					_items.append(ITEMS[item_uid])
		
		if menus.get_menu_by_name('Pick up')>-1:
			menus.delete_menu(menus.get_menu_by_name('Pick up'))
			return False
		
		if not _items:
			gfx.message('There\'s nothing to pick up.')
			
			return False
		
		create_open_item_menu(_items)
	
	if INPUT['b']:
		if WORLD_INFO['time_scale'] == 12:
			WORLD_INFO['time_scale'] = 1
		else:
			WORLD_INFO['time_scale'] = 12
	
	if INPUT['n']:
		import pathfinding
		
		for pos in pathfinding.create_path(LIFE[SETTINGS['controlling']],
		                        LIFE[SETTINGS['controlling']]['pos'],
		                        (LIFE[SETTINGS['controlling']]['pos'][0]-5,
		                         LIFE[SETTINGS['controlling']]['pos'][1]-5,
		                         LIFE[SETTINGS['controlling']]['pos'][2]-5),
		                        [zones.get_zone_at_coords(LIFE[SETTINGS['controlling']]['pos'])]):
			print(pos)
			SELECTED_TILES[0].append((pos[0], pos[1], 2))
	
	#if INPUT['N']:
	#	if not SETTINGS['kill threads']:
	#		logging.debug('Killing threads...')
	#	
	#	SETTINGS['kill threads'] = True
	
	if INPUT['y']:
		_id = int(SETTINGS['following'])
		while _id>1:
			_id -= 1
			if not LIFE[str(_id)]['dead']:
				break
		
		life.focus_on(LIFE[str(_id)])
		SELECTED_TILES[0] = []
		FADE_TO_WHITE[0] = 0
		gfx.refresh_view('map')

	if INPUT['u']:
		_id = int(SETTINGS['following'])
		while _id<len(LIFE):
			_id += 1
			if not LIFE[str(_id)]['dead']:
				break
		
		life.focus_on(LIFE[str(_id)])
		SELECTED_TILES[0] = []
		FADE_TO_WHITE[0] = 0
		gfx.refresh_view('map')

	if INPUT['l']:
		create_look_list()
	
	if INPUT['k']:
		if menus.get_menu_by_name('Crafting')>-1:
			menus.delete_menu(menus.get_menu_by_name('Crafting'))
		else:
			create_crafting_menu()

	if INPUT['1']:
		if LIFE[SETTINGS['controlling']]:
			if LIFE[SETTINGS['controlling']]['targeting']:
				LIFE[SETTINGS['controlling']]['targeting'][0]-=1
				LIFE[SETTINGS['controlling']]['targeting'][1]+=1
			else:
				life.clear_actions(LIFE[SETTINGS['controlling']])
				life.add_action(LIFE[SETTINGS['controlling']],
				                {'action': 'move',
				                 'to': (LIFE[SETTINGS['controlling']]['pos'][0]-1, LIFE[SETTINGS['controlling']]['pos'][1]+1, LIFE[SETTINGS['controlling']]['pos'][2])},
				                200)
		else:
			CAMERA_POS[2] = 1

	if INPUT['2']:
		if not LIFE[SETTINGS['controlling']]:
			CAMERA_POS[2] = 2

	if INPUT['3']:
		if LIFE[SETTINGS['controlling']]:
			if LIFE[SETTINGS['controlling']]['targeting']:
				LIFE[SETTINGS['controlling']]['targeting'][0]+=1
				LIFE[SETTINGS['controlling']]['targeting'][1]+=1
			else:
				life.clear_actions(LIFE[SETTINGS['controlling']])
				life.add_action(LIFE[SETTINGS['controlling']],
				                {'action': 'move',
				                 'to': (LIFE[SETTINGS['controlling']]['pos'][0]+1, LIFE[SETTINGS['controlling']]['pos'][1]+1, LIFE[SETTINGS['controlling']]['pos'][2])},
				                200)
		else:
			CAMERA_POS[2] = 3

	if INPUT['4']:
		if not LIFE[SETTINGS['controlling']]:
			CAMERA_POS[2] = 4

	if INPUT['5']:
		if not LIFE[SETTINGS['controlling']]:
			CAMERA_POS[2] = 5
	
	if INPUT['7']:
		if LIFE[SETTINGS['controlling']]:
			if LIFE[SETTINGS['controlling']]['targeting']:
				LIFE[SETTINGS['controlling']]['targeting'][0]-=1
				LIFE[SETTINGS['controlling']]['targeting'][1]-=1
			else:
				life.clear_actions(LIFE[SETTINGS['controlling']])
				life.add_action(LIFE[SETTINGS['controlling']],
				                {'action': 'move',
				                 'to': (LIFE[SETTINGS['controlling']]['pos'][0]-1, LIFE[SETTINGS['controlling']]['pos'][1]-1, LIFE[SETTINGS['controlling']]['pos'][2])},
				                200)
	if INPUT['9']:
		if LIFE[SETTINGS['controlling']]:
			if LIFE[SETTINGS['controlling']]['targeting']:
				LIFE[SETTINGS['controlling']]['targeting'][0]+=1
				LIFE[SETTINGS['controlling']]['targeting'][1]-=1
			else:
				life.clear_actions(LIFE[SETTINGS['controlling']])
				life.add_action(LIFE[SETTINGS['controlling']],
				                {'action': 'move',
				                 'to': (LIFE[SETTINGS['controlling']]['pos'][0]+1, LIFE[SETTINGS['controlling']]['pos'][1]-1, LIFE[SETTINGS['controlling']]['pos'][2])},
				                200)

def inventory_select(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_item_uid = entry['id']
	_item = life.get_inventory_item(LIFE[SETTINGS['following']], _item_uid)
	_menu_items = []
	
	if 'storing' in _item and not 'is_item' in entry:
		_stored_items = life.get_custom_fancy_inventory_menu_items(LIFE[SETTINGS['following']], _item['storing'])
		
		_i = menus.create_menu(title=items.get_name(_item),
		                       menu=_stored_items,
		                       padding=(1,1),
		                       position=(1,1),
		                       format_str='[$i] $k',
		                       on_select=inventory_select,
		                       action=MENUS[ACTIVE_MENU['menu']]['action'])
		menus.activate_menu(_i)
	else:
		handle_inventory_item_select(entry)

def handle_inventory_item_select(entry):
	_item_uid = entry['id']
	_item = life.get_inventory_item(LIFE[SETTINGS['controlling']], _item_uid)
	_menu_items = []
	
	if MENUS[ACTIVE_MENU['menu']]['action']:
		entry['key'] = MENUS[ACTIVE_MENU['menu']]['action']
		
		return handle_inventory_item_select_action(entry)
	
	if life.item_is_equipped(LIFE[SETTINGS['controlling']], _item_uid):
		_menu_items.append(menus.create_item('single',
			        'Unequip',
			        None,
			        id=_item_uid))
	else:
		_menu_items.append(menus.create_item('single',
			        'Equip',
			        None,
			        id=_item_uid))
	
	_menu_items.append(menus.create_item('single',
			        'Drop',
			        None,
			        id=_item_uid))
	
	_menu_items.append(menus.create_item('single',
			        'Throw',
			        None,
			        id=_item_uid))
	
	_i = menus.create_menu(title='Action',
		                       menu=_menu_items,
		                       padding=(1,1),
		                       position=(1,1),
		                       format_str='$k',
		                       on_select=handle_inventory_item_select_action)
	menus.activate_menu(_i)
	
def handle_inventory_item_select_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_item_uid = entry['id']
	_item = life.get_inventory_item(LIFE[SETTINGS['controlling']], _item_uid)
	
	if key == 'Equip':
		inventory_equip(entry)
	elif key == 'Unequip':
		return inventory_unequip_action(entry)
	elif key == 'Drop':
		inventory_drop(entry)
	elif key == 'Throw':
		return inventory_throw(entry)
	
	menus.delete_active_menu()
	menus.delete_active_menu()

def inventory_equip(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item_uid = entry['id']
	
	_item = life.get_inventory_item(LIFE[SETTINGS['controlling']], item_uid)
	
	if _item['type'] == 'gun' and not life.can_hold_item(LIFE[SETTINGS['controlling']]):
		gfx.message('You can\'t possibly hold that!')
		
		return False
	
	life.add_action(LIFE[SETTINGS['controlling']],{'action': 'equipitem',
		'item': item_uid},
		200,
		delay=life.get_item_access_time(LIFE[SETTINGS['controlling']], item_uid))
	
	if 'CAN_WEAR' in _item['flags']:
		gfx.message('You start putting on %s.' % items.get_name(_item))
	else:
		gfx.message('You begin handling %s.' % items.get_name(_item))
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_unequip(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['item']['uid']
	
	_item = life.get_inventory_item(LIFE[SETTINGS['controlling']],item)
	_delay = life.get_item_access_time(LIFE[SETTINGS['controlling']], entry['item']['uid'])
	_delay += life.get_item_access_time(LIFE[SETTINGS['controlling']], entry['container'])
	
	life.add_action(LIFE[SETTINGS['controlling']],{'action': 'storeitem',
		'item': item,
		'container': entry['container']},
		200,
		delay=_delay)
	
	gfx.message('You begin storing %s.' % items.get_name(_item))
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_unequip_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['id']
	
	_item = life.get_inventory_item(LIFE[SETTINGS['controlling']],item)
	_menu = []
	
	for container in life.get_all_storage(LIFE[SETTINGS['controlling']]):		
		if container['capacity']+_item['size'] > container['max_capacity']:
			continue
		
		if container['uid'] == item:
			continue
		
		_menu.append(menus.create_item('single',
			container['name'],
			'%s/%s' % (container['capacity'],container['max_capacity']),
			container=container['uid'],
			item=_item))
	
	if not _menu:
		gfx.message('You have nowhere to store this item!')
		
		return False
	
	_i = menus.create_menu(title='Store in...',
		menu=_menu,
		padding=(1,1),
		position=(1,1),
		format_str='  $k: $v',
		on_select=inventory_unequip)
	
	menus.activate_menu(_i)

def inventory_drop(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']], entry['id'])
	
	_name = items.get_name(item)
	
	life.add_action(LIFE[SETTINGS['controlling']],{'action': 'dropitem',
		'item': item['uid']},
		200,
		delay=life.get_item_access_time(LIFE[SETTINGS['controlling']], item['uid']))
	
	gfx.message('You start to drop %s.' % _name)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_eat(entry):
	key = entry['key']
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']], entry['id'])
	
	life.add_action(LIFE[SETTINGS['controlling']],{'action': 'consumeitem',
		'item': item['uid']},
		200,
		delay=life.get_item_access_time(LIFE[SETTINGS['controlling']], item['uid']))
	
	if item['type'] == 'food':
		gfx.message('You start to eat %s.' % items.get_name(item))
	elif item['type'] == 'drink':
		gfx.message('You start to drink %s.' % items.get_name(item))
	elif item['type'] == 'medicine':
		gfx.message('You start to take %s.' % items.get_name(item))
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_throw(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = ITEMS[entry['id']]
	
	_hand = life.is_holding(LIFE[SETTINGS['controlling']], entry['id'])
	if _hand:
		LIFE[SETTINGS['controlling']]['targeting'] = LIFE[SETTINGS['controlling']]['pos'][:]
		LIFE[SETTINGS['controlling']]['throwing'] = item['uid']
		menus.delete_menu(ACTIVE_MENU['menu'])
		
		return True
	
	_hand = life.can_throw(LIFE[SETTINGS['controlling']])
	if not _hand:
		gfx.message('Both of your hands are full.')
	
		menus.delete_menu(ACTIVE_MENU['menu'])
		return False

	_stored = life.item_is_stored(LIFE[SETTINGS['controlling']], item['uid'])
	if _stored:
		_delay = 15
		gfx.message('You start to remove %s from %s.' % (items.get_name(item), items.get_name(_stored)))
	else:
		_delay = 8
	
	LIFE[SETTINGS['controlling']]['throwing'] = item['uid']
	
	if item['type'] == 'explosive':
		if 'player' in LIFE[SETTINGS['controlling']]:
			menus.delete_menu(ACTIVE_MENU['menu'])
			_items = [menus.create_item('list', 'Time', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], item=item['uid'])]
			_menu = menus.create_menu(title='Arm',
					                  menu=_items,
					                  padding=(1,1),
					                  position=(1,1),
					                  format_str='$k: $v',
					                  on_select=handle_arm_item)
			
			menus.activate_menu(_menu)
	else:
		menus.delete_menu(ACTIVE_MENU['menu'])
	
		life.add_action(LIFE[SETTINGS['controlling']],{'action': 'holditemthrow',
			'item': entry['id'],
			'hand': _hand},
			200,
			delay=_delay)
	
def handle_arm_item(entry):
	key = entry['key']
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']], entry['item'])
	value = entry['values'][entry['value']]
	_hand = life.can_throw(LIFE[SETTINGS['controlling']])
	
	timers.create(item, action.make_small_script(function='explode',
	                                       item=item['uid']),
	              15+value)
	
	life.add_action(LIFE[SETTINGS['controlling']],{'action': 'holditemthrow',
			'item': entry['item'],
			'hand': _hand},
			200,
			delay=15)
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def target_view(entry):
	life.focus_on(LIFE[entry['target']])
	LIFE[SETTINGS['controlling']]['targeting'] = LIFE[entry['target']]['pos'][:]

def inventory_fire(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']],entry['id'])
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	
	LIFE[SETTINGS['controlling']]['firing'] = item
	
	if not life.is_holding(LIFE[SETTINGS['controlling']],entry['id']):
		_hand = life.can_throw(LIFE[SETTINGS['controlling']])
		
		if not _hand:
			gfx.message('Both of your hands are full.')
		
			menus.delete_menu(ACTIVE_MENU['menu'])
			return False
	
	_menu_items = menus.create_target_list()
	
	if not _menu_items:
		gfx.message('You have nothing to aim at!')
		
		return False

	_i = menus.create_menu(title='Aim at...',
          menu=_menu_items,
          padding=(1,1),
          position=(1,1),
          format_str='$k',
          on_select=inventory_fire_select_limb,
          on_close=exit_target,
          on_move=target_view)

	menus.activate_menu(_i)

def inventory_fire_select_limb(entry, no_delete=False):	
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if not no_delete:
		menus.delete_menu(ACTIVE_MENU['menu'])
	
	_limbs = []
	for limb in LIFE[entry['target']]['body']:
		_held_items = []
		
		for held_item_id in LIFE[entry['target']]['body'][limb]['holding']:
			_held_items.append(items.get_item_from_uid(held_item_id)['name'])
		
		if not _held_items:
			_held_items = ['Exposed']
			
		_limbs.append(menus.create_item('single',
			limb,
			', '.join(_held_items),
			target=LIFE[entry['target']],
			limb=limb))
		
	_i = menus.create_menu(title='Select Limb',
		menu=_limbs,
		padding=(1,1),
		position=(1,1),
		on_select=inventory_fire_action,
		on_close=exit_target,
		format_str='$k: $v')
	
	menus.activate_menu(_i)

def inventory_fire_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	for i in range(weapons.get_rounds_to_fire(weapons.get_weapon_to_fire(LIFE[SETTINGS['controlling']]))):
		life.add_action(LIFE[SETTINGS['controlling']],{'action': 'shoot',
		    'target': entry['target']['pos'],
		    'target_id': entry['target']['id'],
		    'limb': entry['limb']},
			5000-i,
		     delay=bad_numbers.clip(i, 0, 1)*3)
		
	LIFE[SETTINGS['controlling']]['targeting'] = None
	life.focus_on(LIFE[SETTINGS['controlling']])
	SELECTED_TILES[0] = []
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_change_fire_rate(entry):
	key = entry['key']
	weapon = ITEMS[entry['item']]
	
	_fire_modes = []
	
	for fire_mode in weapon['firemodes']:
		_fire_modes.append(menus.create_item('single',
			     fire_mode,
			     None,
			     item=entry['item']))
	
	_i = menus.create_menu(title='Change to...',
		menu=_fire_modes,
		padding=(1,1),
		position=(1,1),
		on_select=inventory_change_fire_rate_action,
		format_str='$k')
	
	menus.activate_menu(_i)

def inventory_change_fire_rate_action(entry):
	key = entry['key']
	weapon = ITEMS[entry['item']]
	firemode = weapon['firemodes'].index(key)
	
	weapons.change_fire_mode(weapon, firemode)
	gfx.message('Changed fire rate for %s: %s' % (weapon['name'], key))
	
	menus.delete_active_menu()
	menus.delete_active_menu()

def mouse_select_item_at():
	_m_x, _m_y = inputs.get_mouse_location()
	
	_items = items.get_items_at((_m_x, _m_y, 2))
	
	if not _items:
		return False
	
	_index = menus.get_menu_index_by_flag(ACTIVE_MENU['menu'], 'item', _items[0]['uid'])
	
	if _index == -1:
		return False
	
	menus.go_to_menu_index(ACTIVE_MENU['menu'], _index)
	#print _m_x, _m_y

def delete_look_list(entry):
	SELECTED_TILES[0] = []
	menus.delete_menu(menus.get_menu_by_name('Examining...'))
	inputs.set_mouse_move_callback(None)
	
	gfx.enable_panels()

def create_look_list():
	#inputs.set_mouse_click_callback(1, mouse_select_item_at)
	inputs.set_mouse_move_callback(mouse_select_item_at)
	
	if menus.get_menu_by_name('Look at...')>-1:
		SELECTED_TILES[0] = []
		menus.delete_menu(menus.get_menu_by_name('Look at...'))
		menus.delete_menu(menus.get_menu_by_name('Examining...'))
		inputs.set_mouse_move_callback(None)
		gfx.enable_panels()
		return False
	
	_menu_items = []
	for item in [l for l in list(ITEMS.values()) if sight.can_see_position(LIFE[SETTINGS['controlling']], l['pos']) and not l == LIFE[SETTINGS['controlling']]]:
		if items.is_item_owned(item['uid']):
			continue
		
		_menu_items.append(menus.create_item('single', item['name'], None, item=item['uid'], icon=item['icon']))
	
	for target in [l for l in list(LIFE.values()) if sight.can_see_position(LIFE[SETTINGS['controlling']], l['pos']) and not l == LIFE[SETTINGS['controlling']]]:
		_menu_items.append(menus.create_item('single', ' '.join(target['name']), None, target=target['id'], icon=target['icon']))
	
	if not _menu_items:
		gfx.message('There\'s nothing to look at.')
		return False
	
	gfx.disable_panels()
	
	_i = menus.create_menu(title='Look at...',
	    menu=_menu_items,
	    padding=(1, 1),
	    position=(MAP_WINDOW_SIZE[0], 1),
	    on_move=handle_view,
	    on_close=delete_look_list,
	    format_str='[$i] $k')
	
	menus.activate_menu(_i)

def create_dialog(entry):
	_target = entry['target']
	LIFE[SETTINGS['controlling']]['targeting'] = None
	SELECTED_TILES[0] = []

	_dialog = dialog.create_dialog_with(LIFE[SETTINGS['controlling']], _target)
	dialog.say_via_gist(LIFE[SETTINGS['controlling']], _dialog, 'start_conversation')
	
	menus.delete_active_menu()

def exit_target(entry):
	life.focus_on(LIFE[SETTINGS['controlling']])
	LIFE[SETTINGS['controlling']]['targeting'] = None
	SELECTED_TILES[0] = []

def inventory_reload(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']],entry['id'])
	
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
		for _weapon in life.get_held_items(LIFE[SETTINGS['controlling']],matches=[{'type': 'gun','ammotype': item['ammotype'],'feed': item['type']}]):
			weapon = life.get_inventory_item(LIFE[SETTINGS['controlling']],_weapon)
			
			if weapons.get_feed(weapon):
				continue
			
			_weapons.append(menus.create_item('single',weapon['name'],None,ammo=item,id=weapon['uid']))
		
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
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']],entry['id'])
	
	if key == 'Remove feed':
		life.add_action(LIFE[SETTINGS['controlling']],{'action': 'unload',
			'weapon': entry['id']},
			200,
			delay=20)
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_handle_ammo(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']],entry['id'])
	
	if key == 'Fill':
		if not item['uid'] in life.get_held_items(LIFE[SETTINGS['controlling']]):
			if not life.can_hold_item(LIFE[SETTINGS['controlling']]):
				gfx.message('You need a hand free to fill the %s with %s rounds.' % (item['type'],item['ammotype']))
				return False
		
		life.add_action(LIFE[SETTINGS['controlling']],{'action': 'removeandholditem',
			'item': item['uid']},
			200,
			delay=20)
		
		gfx.message('You start filling the %s with %s rounds.' % (item['type'],item['ammotype']))
	
		_rounds = len(item['rounds'])
		for ammo in life.get_all_inventory_items(LIFE[SETTINGS['controlling']],matches=[{'type': 'bullet', 'ammotype': item['ammotype']}]):
			life.add_action(LIFE[SETTINGS['controlling']],{'action': 'refillammo',
				'ammo': item,
				'round': ammo},
				200,
				delay=3)
			
			_rounds += 1
			
			if _rounds>=item['maxrounds']:
				break
	else:
		life.add_action(LIFE[SETTINGS['controlling']],{'action': 'reload',
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
	item = life.get_inventory_item(LIFE[SETTINGS['controlling']],entry['id'])
	
	gfx.message('You start filling the %s with %s rounds.' % (item['type'],item['ammotype']))
	
	_rounds = len(item['rounds'])
	for ammo in life.get_all_inventory_items(LIFE[SETTINGS['controlling']],matches=[{'type': 'bullet', 'ammotype': item['ammotype']}]):
		life.add_action(LIFE[SETTINGS['controlling']],{'action': 'refillammo',
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
	#_items = items.get_items_at(LIFE[SETTINGS['controlling']]['pos'])
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])
	
	_item = items.get_item_from_uid(entry['item'])
	
	#TODO: Lowercase menu keys
	if entry['key'] == 'Equip':
		if entry['values'][entry['value']] == 'Wear':
			if not life.can_wear_item(LIFE[SETTINGS['controlling']], _item['uid']):
				gfx.message('You can\'t equip this item!')
				return False
			
			gfx.message('You start to pick up %s.' % items.get_name(_item))
			
			life.add_action(LIFE[SETTINGS['controlling']],{'action': 'pickupequipitem',
				'item': entry['item']},
				200,
				delay=life.get_item_access_time(LIFE[SETTINGS['controlling']], _item['uid']))
		
		elif entry['values'][entry['value']] in LIFE[SETTINGS['controlling']]['hands']:
			gfx.message('You start to pick up %s.' % items.get_name(_item))
			
			life.add_action(LIFE[SETTINGS['controlling']],{'action': 'pickupholditem',
				'item': entry['item'],
				'hand': entry['values'][entry['value']]},
				200,
				delay=life.get_item_access_time(LIFE[SETTINGS['controlling']], _item['uid']))
		
		return True
	
	if not life.can_carry_item(LIFE[SETTINGS['controlling']], entry['item']):
		gfx.message('You can\'t lift the %s.' % _item['name'])
		return False
	
	gfx.message('You start to put %s in %s.' %
		(items.get_name(items.get_item_from_uid(entry['item'])), items.get_name(items.get_item_from_uid(entry['container']))))
	
	life.add_action(LIFE[SETTINGS['controlling']],{'action': 'pickupitem',
		'item': entry['item'],
		'container': entry['container']},
		200,
		delay=life.get_item_access_time(LIFE[SETTINGS['controlling']], entry['item']))
	
	return True

def pick_up_item_from_ground_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_item = items.get_item_from_uid(entry['item'])
	
	_menu = []
	#TODO: Can we equip this?
	_menu.append(menus.create_item('title','Actions',None,enabled=False))
	_menu.append(menus.create_item('single','Equip','Wear',item=entry['item']))
	
	for hand in LIFE[SETTINGS['controlling']]['hands']:
		_menu.append(menus.create_item('single','Equip',hand,item=entry['item']))
	
	_menu.append(menus.create_item('title','Store in...',None,enabled=False))
	for container in life.get_all_storage(LIFE[SETTINGS['controlling']]):
		if container['capacity']+_item['size'] > container['max_capacity']:
			_enabled = False
		else:
			_enabled = True
		
		_menu.append(menus.create_item('single',
			container['name'],
			'%s/%s' % (container['capacity'],container['max_capacity']),
			container=container['uid'],
			enabled=_enabled,
			item=entry['item']))
	
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
		_menu_items.append(menus.create_item('single', item['name'], None, icon=item['icon'], item=item['uid']))
	
	_i = menus.create_menu(title='Pick up',
		menu=_menu_items,
		padding=(1,1),
		position=(1,1),
		format_str='[$i] $k',
		on_select=pick_up_item_from_ground_action)
	
	menus.activate_menu(_i)

def create_open_item_menu(items):
	_menu_items = []
	_items = []
	
	for item in items:
		if not 'storing' in item:
			continue
		
		_menu_items.append(menus.create_item('title', item['name'], None, icon=item['icon'], item=item['uid']))
		
		for stored_item in [ITEMS[s] for s in item['storing']]:
			_menu_items.append(menus.create_item('single', stored_item['name'], None, icon=stored_item['icon'], item=stored_item['uid']))
			_items.append(stored_item['uid'])
	
	if len(_menu_items)==1:
		gfx.message('The %s is empty.' % items[0]['name'])
		return False
	
	if not _items:
		gfx.message('There is nothing here to open.')
		return False
	
	_i = menus.create_menu(title='Pick up',
		menu=_menu_items,
		padding=(1,1),
		position=(1,1),
		format_str='[$i] $k',
		on_select=pick_up_item_from_ground_action)
	
	menus.activate_menu(_i)

def return_to_inventory(entry):
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.activate_menu_by_name('Inventory')

def handle_options_menu(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Save':
		worldgen.save_world()
	elif key == 'Load':
		worldgen.load_world(WORLD_INFO['id'])
	elif key == 'Reload map':
		logging.warning('Map reloading is not well tested!')
		global MAP
		del MAP
		
		maps.load_map('map1.dat')
		
		logging.warning('Redrawing LOS.')
		maps._render_los(MAP,PLAYER['pos'],cython=CYTHON_ENABLED)
	elif key == 'Update chunk map':
		maps.update_chunk_map()
	elif key == 'Show camp ownership':
		camps.debug_camps()
	elif key == 'Drop cache':
		debug.drop()
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def handle_options_menu_change(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Show visible chunks':
		SETTINGS['draw visible chunks'] = (value=='on')

def handle_jobs_menu_action(entry):
	if entry['key'] == 'Join':
		jobs.join_job(entry['job_id'], SETTINGS['controlling'])
		LIFE[SETTINGS['controlling']]['task'] = jobs.get_next_task(LIFE[SETTINGS['controlling']], entry['job_id'])
	else:
		jobs.leave_job(entry['job_id'], SETTINGS['controlling'])
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def handle_jobs_menu(entry):
	if 'job_id' in entry:
		_menu_items = [menus.create_item('single', 'Join', None, job_id=entry['job_id'])]
		_menu_items.append(menus.create_item('single', 'Decline', None, job_id=entry['job_id']))	
	
		_i = menus.create_menu(title='Action',
			menu=_menu_items,
			padding=(1,1),
			position=(1,1),
			format_str='$k',
			on_select=handle_jobs_menu_action)
		
		menus.activate_menu(_i)

def handle_tasks_menu(entry):
	if entry['key'] == 'Quit':
		jobs.leave_job(entry['job_id'], SETTINGS['controlling'], reject=True)
		
		menus.delete_menu(ACTIVE_MENU['menu'])

def handle_advanced_movement(entry):
	_target = entry['target']
	_move = entry['key']
	
	menus.delete_active_menu()	
	
	melee.fight(LIFE[SETTINGS['controlling']], _target)

def handle_view(entry):
	if 'item' in entry:
		handle_item_view(entry)
		return
	
	handle_life_view(entry)

def handle_item_view(entry):
	item = items.get_item_from_uid(entry['item'])
	
	if menus.get_menu_by_name('Examining...')>-1:
		menus.delete_menu(menus.get_menu_by_name('Equip'))
	
	SELECTED_TILES[0] = [tuple(item['pos'])]
	_menu_items = []
	
	for key in item['examine_keys']:
		_key = key
		
		if key == 'description':
			_key = item['name']
		
		_menu_items.append(menus.create_item('single', _key, item[key]))	

	_i = menus.create_menu(title='Examining...',
        menu=_menu_items,
        padding=(1, 1),
        position=(-1, -4),
	   alignment='botleft',
	   on_select=lambda entry: menus.delete_menu(menus.get_menu_by_name('Examining...')),
        format_str='$k: $v')

def handle_life_view(entry):
	target = LIFE[entry['target']]
	
	if menus.get_menu_by_name('Examining...')>-1:
		menus.delete_menu(menus.get_menu_by_name('Equip'))
	
	SELECTED_TILES[0] = [tuple(target['pos'])]
	_menu_items = []
	
	#for key in target['examine_keys']:
	#	_menu_items.append(menus.create_item('single', key, item[key]))
	for limb in LIFE[entry['target']]['body']:
		_held_items = []
		
		for held_item_id in LIFE[entry['target']]['body'][limb]['holding']:
			_held_items.append(items.get_item_from_uid(held_item_id)['name'])
		
		if not _held_items:
			_held_items = ['Exposed']
			
		_menu_items.append(menus.create_item('single',
			limb,
			', '.join(_held_items),
			target=LIFE[entry['target']],
			limb=limb))

	_i = menus.create_menu(title='Examining...',
        menu=_menu_items,
        padding=(1, 1),
        position=(-1, 1),
        alignment='botleft',
        format_str='$k: $v',
	   dim=False)

def create_jobs_menu():
	if menus.get_menu_by_name('Jobs')>-1:
		menus.delete_menu(menus.get_menu_by_name('Jobs'))
		return False
	
	_all_jobs = LIFE[SETTINGS['controlling']]['jobs']
	if not _all_jobs:
		gfx.message('You don\'t have any jobs.')
		return False
	
	_jobs = [menus.create_item('title', 'Jobs', None)]
	
	for job in [jobs.get_job(j) for j in _all_jobs]:
		_jobs.append(menus.create_item('single', job['name'], job['description'], job_id=job['id']))
	
	if _jobs:
		_i = menus.create_menu(title='Jobs',
	                           menu=_jobs,
	                           padding=(1,1),
	                           position=(1,1),
	                           format_str='$k: $v',
	                           on_select=handle_jobs_menu)
	
		menus.activate_menu(_i)

def create_tasks_menu():
	if menus.get_menu_by_name('Tasks')>-1:
		menus.delete_menu(menus.get_menu_by_name('Tasks'))
		return False
	
	_life = LIFE[SETTINGS['controlling']]
	_tasks = []
	
	for task_id in list(jobs.get_job(_life['job'])['tasks'].keys()):
		task = jobs.get_task(_life['job'], task_id)
		
		_tasks.append(menus.create_item('single',
		                                task_id,
		                                task['description'],
		                                job_id=_life['job'],
		                                task_id=task_id,
		                                enabled=(task_id in jobs.get_free_tasks(_life['job'], local_completed=_life['completed_tasks']))))
	
	_tasks.append(menus.create_item('title', 'Job', ''))
	_tasks.append(menus.create_item('single', 'Quit', '', job_id=_life['job']))
	
	if _tasks:
		_i = menus.create_menu(title='Tasks',
	                           menu=_tasks,
	                           padding=(1,1),
	                           position=(1,1),
	                           format_str='$k: $v',
		                       on_select=handle_tasks_menu)
	
		menus.activate_menu(_i)

def announce_to(entry):
	if entry['who'] == 'public':
		_announce_to = list(LIFE.keys())
		_announce_to.remove(SETTINGS['controlling'])
	elif entry['who'] == 'trusted':
		_announce_to = judgement.get_trusted(LIFE[SETTINGS['controlling']], visible=False)
	elif entry['who'] == 'private':
		menus.delete_menu(ACTIVE_MENU['menu'])
		menus.delete_menu(ACTIVE_MENU['menu'])
		return False
	
	for life_id in _announce_to:
		speech.communicate(LIFE[SETTINGS['controlling']],
			           'order_to_gather_resources',
			           msg='New group gather at xx,yy',
			           matches=[{'id': life_id}],
			           job_id=entry['job_id'],)
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def create_announce_group_menu(**kwargs):
	_phrases = []
	_phrases.append(menus.create_item('single', 'Private', None, who='private'))
	_phrases.append(menus.create_item('single', 'Public', None, gist='job', who='public', **kwargs))
	_phrases.append(menus.create_item('single', 'Trusted', None, gist='job', who='trusted', **kwargs))
	
	_menu = menus.create_menu(title='Announce group to...',
                              menu=_phrases,
                              padding=(1,1),
                              position=(1,1),
                              format_str='$k',
                              on_select=announce_to)

	menus.activate_menu(_menu)
	
def handle_create_job(entry):
	for entry in entry['workers']:
		_assigned = entry['values'][entry['value']]=='Assigned'
		print(entry['key'], _assigned)

def handle_select_workers(entry):
	job = entry['key']
	
	_workers = []
	for worker in [LIFE[w] for w in groups.get_group(life, LIFE[SETTINGS['controlling']]['group'])['members']]:
		_workers.append(menus.create_item('list', ' '.join(worker['name']), ['Free', 'Assigned'], workers=_workers))
	
	_menu = menus.create_menu(title='Select Workers',
                              menu=_workers,
                              padding=(1,1),
                              position=(1,1),
                              format_str='$k: $v',
                              on_select=handle_create_job)
	
	menus.activate_menu(_menu)

def talk_to(entry):
	speech.communicate(LIFE[SETTINGS['controlling']], 'call', matches=[entry['target']])
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

#TODO: General function
def order_attack(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	speech.announce(LIFE[SETTINGS['controlling']], 'order_attack', group=LIFE[SETTINGS['controlling']]['group'], target=entry['target'])
	
	menus.delete_active_menu()
	menus.delete_active_menu()

def order_status(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	speech.start_dialog(LIFE[SETTINGS['controlling']], entry['target'], 'order_health_report_partner')
	
	menus.delete_active_menu()
	menus.delete_active_menu()

def order_location(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	speech.start_dialog(LIFE[SETTINGS['controlling']], entry['target'], 'order_status_report_partner')
	
	menus.delete_active_menu()
	menus.delete_active_menu()

def send_command(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	#TODO: General function
	if key == 'Attack':
		_menu_items = menus.create_target_list()
		
		if not _menu_items:
			return False
		
		_menu = menus.create_menu(title='Select Target',
		                          menu=_menu_items,
		                          padding=(1,1),
		                          position=(1,1),
		                          format_str='$k: $v',
		                          on_select=order_attack)
		
		menus.activate_menu(_menu)
	elif key == 'Health':
		_group = groups.get_group(LIFE[SETTINGS['controlling']], LIFE[SETTINGS['controlling']]['group'])
		_menu_items = menus._create_target_list(_group['members'])
		
		if not _menu_items:
			return False
		
		_menu = menus.create_menu(title='Check on...',
		                          menu=_menu_items,
		                          padding=(1,1),
		                          position=(1,1),
		                          format_str='$k',
		                          on_select=order_status)
		
		menus.activate_menu(_menu)
	elif key == 'Location':
		_group = groups.get_group(LIFE[SETTINGS['controlling']], LIFE[SETTINGS['controlling']]['group'])
		_menu_items = menus._create_target_list(_group['members'])
		
		if not _menu_items:
			return False
		
		_menu = menus.create_menu(title='Get location of...',
		                          menu=_menu_items,
		                          padding=(1,1),
		                          position=(1,1),
		                          format_str='$k',
		                          on_select=order_location)
		
		menus.activate_menu(_menu)

def radio_menu(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_life = LIFE[SETTINGS['controlling']]
	_pos = life.get_current_chunk(_life)['pos']
	
	if key == 'Distress':
		#speech.announce(life, 'under_attack')
		pass
	elif key == 'Call':
		_people = []
		
		for life_id in LIFE[SETTINGS['controlling']]['know']:
			if _life['group'] and groups.is_leader(LIFE[SETTINGS['controlling']], _life['group'], life_id):
				fg_color = tcod.dark_green
			elif judgement.can_trust(_life, life_id):
				fg_color = tcod.green
			else:
				fg_color = tcod.white
			
			_color = life.draw_life_icon(LIFE[life_id])[1]
			_people.append(menus.create_item('single',
			                                 ' '.join(LIFE[life_id]['name']),
			                                 None,
			                                 target=life_id,
			                                 color=(_color, tcod.color_lerp(_color, tcod.white, 0.5))))
		
		if _people:
			_menu = menus.create_menu(title='Talk to...',
                              menu=_people,
                              padding=(1,1),
                              position=(1,1),
                              format_str='$k',
                              on_select=talk_to)
			menus.activate_menu(_menu)
			return True
		
	elif key == 'Create group':
		_g = groups.create_group(LIFE[SETTINGS['controlling']])
		
		return create_announce_group_menu()
	elif key == 'Announce group':
		return create_announce_group_menu(job_id=groups.get_flag(LIFE[SETTINGS['controlling']]['group'], 'job_gather'))
	elif key == 'Locate':
		speech.communicate(_life,
		                   'group_location',
		                   msg='Where are you?',
		                   matches=[{'id': groups.get_group(life, _life['group'])['leader']}],
		                   group_id=_life['group'])
	elif key == 'Shelter':
		groups.find_and_announce_shelter(_life, _life['group'])
	elif key == 'Manage Jobs':
		_jobs = [menus.create_item('single', 'Free Roam', 'Scout out the area.', job='roam')]
		_jobs.append(menus.create_item('single', 'Guard Area', 'Keep watch over a specific point.', job='guard_area'))
		_jobs.append(menus.create_item('single', 'Guard Person', 'Protect a target.', job='guard_person'))
		
		_menu = menus.create_menu(title='Manage Jobs',
		                          menu=_jobs,
		                          padding=(1,1),
		                          position=(1,1),
		                          format_str='$k: $v',
		                          on_select=handle_select_workers)
		
		return menus.activate_menu(_menu)
	elif key == 'Suggest location':
		pass
	#TODO: Steve "Jobs" Jobbers
	elif key == 'Jobs':
		speech.communicate(_life,
		                   'group_jobs',
		                   msg='Do you have any jobs for me?',
		                   matches=[{'id': groups.get_group(life, _life['group'])['leader']}],
		                   group_id=_life['group'])
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def create_radio_menu():
	_phrases = []
	#_phrases.append(menus.create_item('single', 'Distress', 'Radio for help.'))
	
	if LIFE[SETTINGS['controlling']]['know']:
		_phrases.append(menus.create_item('single', 'Call', 'Contact someone.'))
	
	if not LIFE[SETTINGS['controlling']]['group'] or not groups.is_leader(LIFE[SETTINGS['controlling']], LIFE[SETTINGS['controlling']]['group'], SETTINGS['controlling']):
		_phrases.append(menus.create_item('single', 'Create group', 'Start a new group.'))
	elif groups.is_leader(LIFE[SETTINGS['controlling']], LIFE[SETTINGS['controlling']]['group'], SETTINGS['controlling']):
		_phrases.append(menus.create_item('single', 'Announce group', 'Broadcast for more members.'))
	
	if LIFE[SETTINGS['controlling']]['group']:
		if groups.is_leader(LIFE[SETTINGS['controlling']], LIFE[SETTINGS['controlling']]['group'], SETTINGS['controlling']):
			_phrases.append(menus.create_item('title', 'Group (Leader)', None))
			_phrases.append(menus.create_item('single', 'Manage Jobs', 'Create and view jobs.'))
			_phrases.append(menus.create_item('single', 'Shelter', 'Set this location as a shelter.'))
		else:
			_phrases.append(menus.create_item('title', 'Group (Member)', None))
			_phrases.append(menus.create_item('single', 'Locate', 'Find leader location.'))
			_phrases.append(menus.create_item('single', 'Suggest location', 'Suggest shelter location.'))
			
			if LIFE[SETTINGS['controlling']]['group']:
				_phrases.append(menus.create_item('single', 'Jobs', 'Ask for work.', enabled=len(groups.get_group(LIFE[SETTINGS['controlling']], LIFE[SETTINGS['controlling']]['group'])['members'])>1))
	
	_menu = menus.create_menu(title='Radio',
		menu=_phrases,
		padding=(1,1),
		position=(1,1),
		format_str='$k: $v',
		on_select=radio_menu)
	
	menus.activate_menu(_menu)

def craft_menu_action(entry):
	_player = LIFE[SETTINGS['controlling']]
	_item = ITEMS[entry['item_uid']]
	_recipe = entry['recipe']
	
	crafting.perform_recipe(_player, _item, _recipe)
	
	menus.delete_active_menu()
	menus.delete_active_menu()

def craft_menu_response(entry):
	_player = LIFE[SETTINGS['controlling']]
	_item = ITEMS[entry['item_uid']]
	_menu_items = []
	
	for recipe in _item['craft']:
		_difficulty = 0
		_difficulty_string = ''
		
		if recipe['type'] == 'create_item':
			if not crafting.meets_requirements(_player, recipe['requirements']):
				continue
			
			_difficulty = -crafting.get_recipe_difficulty(_player, _item, recipe)
			
			if _difficulty<=-3:
				_difficulty_string = 'Hard'
				_menu_item_color = tcod.crimson
			elif _difficulty<0:
				_difficulty_string = 'Doable'
				_menu_item_color = tcod.light_green
			else:
				_difficulty_string = 'Easy'
				_menu_item_color = tcod.green
			
			_menu_items.append(menus.create_item('single',
			                                     recipe['name'],
			                                     _difficulty_string,
			                                     item_uid=_item['uid'],
			                                     recipe=recipe,
			                                     color=(_menu_item_color, tcod.color_lerp(tcod.white, _menu_item_color, .5))))
	
	_menu = menus.create_menu(title='Craft',
	                          menu=_menu_items,
	                          padding=(1,1),
	                          position=(1,1),
	                          format_str='$k: $v',
	                          on_select=craft_menu_action)
	
	menus.activate_menu(_menu)
	
	#menus.delete_menu(ACTIVE_MENU['menu'])

def create_crafting_menu():
	_items = []
	_item_names = {}
	
	for item in [items.get_item_from_uid(i) for i in crafting.get_items_for_crafting(LIFE[SETTINGS['controlling']])]:
		if item['name'] in _item_names:
			_item_names[item['name']]['values'][_item_names[item['name']]['value']] += 1
			
			continue
		
		_menu_item = menus.create_item('single',
		                               item['name'],
		                               1,
		                               item_uid=item['uid'])
		_items.append(_menu_item)
		_item_names[item['name']] = _menu_item
		
	#for item in [items.get_item_from_uid(i) for i in crafting.get_items_for_dismantle(LIFE[SETTINGS['controlling']])]:
	#	_items.append(menus.create_item('single',
	#	                                item['name'],
	#	                                None,
	#	                                item_uid=item['uid'],
	#	                                action='dismantle'))
	
	if _items:
		_items.insert(0, menus.create_item('title', 'Dismantle', None, enabled=False))
	else:
		gfx.message('You have no items to modify!')
		return False
	
	_menu = menus.create_menu(title='Crafting',
	                          menu=_items,
	                          padding=(1,1),
	                          position=(1,1),
	                          format_str='($vx) $k',
	                          on_select=craft_menu_response)
	
	menus.activate_menu(_menu)

def create_wound_menu(target):
	_has_wound = False
	_entries = []
	
	for limb in list(LIFE[target]['body'].values()):
		_title = False
		
		for wound in limb['wounds']:
			_limb = life.get_limb(LIFE[target], wound['limb'])
			
			if not _title:					
				_entries.append(menus.create_item('title', wound['limb'], None))
				_title = True
			
			if wound['cut']:
				_cut_amount = wound['cut']/float(_limb['size'])
				
				if _cut_amount <= .2:
					_status = 'Scraped'
				elif _cut_amount <= .45:
					_status = 'Cut'
				elif _cut_amount <= .7:
					_status = 'Gouged'
				else:
					_status = 'Devastated'
				
				_entries.append(menus.create_item('single',
				                                  'Cut',
				                                  _status,
				                                  target=target,
				                                  limb=wound['limb'],
				                                  color=(tcod.color_lerp(tcod.white, tcod.crimson, bad_numbers.clip(_cut_amount, 0.4, 1)),
				                                         tcod.color_lerp(tcod.white, tcod.crimson, bad_numbers.clip(_cut_amount, 0.4, 1)/2))))
				_has_wound = True
	
	if not _has_wound:
		gfx.message('You don\'t need medical attention.')
		
		return False
	
	_i = menus.create_menu(title='Wounds (%s)' % len(_entries),
        menu=_entries,
        padding=(1,1),
        position=(1,1),
        format_str='$k: $v',
        on_select=wound_examine)
	
	menus.activate_menu(_i)		

def create_target_wound_menu(entry):
	create_wound_menu(entry['target'])

def heal_wound(entry):
	_target = entry['target']
	
	life.heal_limb(LIFE[SETTINGS['controlling']], entry['limb'], entry['item_uid'], target=_target)
	
	if _target == SETTINGS['controlling']:
		gfx.message('You start applying %s to your %s.' % (items.get_name(ITEMS[entry['item_uid']]), entry['limb']))
	else:
		gfx.message('You start applying %s to %s\'s %s.' % (items.get_name(ITEMS[entry['item_uid']]), ' '.join(LIFE[_target]['name']), entry['limb']))
	
	while MENUS:
		menus.delete_menu(ACTIVE_MENU['menu'])

def wound_examine(entry):
	_target = entry['target']
	_injury = entry['key'].lower()
	_limb = entry['limb']
	_entries = []
	
	if _injury == 'cut':
		for item in life.get_all_inventory_items(LIFE[SETTINGS['controlling']], matches=[{'type': 'fabric'}]):
			_entries.append(menus.create_item('single', item['name'], item['thickness'], limb=_limb, item_uid=item['uid'], target=_target))
	
	if not _entries:
		gfx.message('You have nothing to treat the %s with.' % _injury)
		return False
	
	_menu = menus.create_menu(title='Heal',
		menu=_entries,
		padding=(1,1),
		position=(1,1),
		format_str='$k: $v',
		on_select=heal_wound)
	
	menus.activate_menu(_menu)

def create_tracking_menu(start_index=-1):
	_player = LIFE[SETTINGS['controlling']]
	_targets = []
	
	for target_id in _player['know']:
		_target = _player['know'][target_id]
		
		if _target['dead']:
			continue
		
		_color = life.draw_life_icon(_target['life'])
		_tracking_color = _color[1]
		
		if judgement.is_tracking(_player, target_id):
			_tracking = 'x'
		else:
			_tracking = ' '
		
		_targets.append(menus.create_item('single',
		                                  _tracking,
		                                  ' '.join(_target['life']['name']),
		                                  color=(_tracking_color, tcod.color_lerp(_tracking_color, tcod.white, .8)),
		                                  target_id=target_id,
		                                  menu_index=len(_targets)+1))
	
	if not _targets:
		gfx.message('There is nobody to track.')
		
		return False
	
	_i = menus.create_menu(title='Track',
	                       menu=_targets,
	                       format_str='[$k] $v',
	                       on_select=toggle_tracking)
	
	menus.activate_menu(_i)
	
	if start_index>=len(_targets):
		menus.get_menu(_i)['index'] = 1
	else:
		menus.get_menu(_i)['index'] = start_index

def toggle_tracking(entry):
	menus.delete_active_menu()
	
	if judgement.is_tracking(LIFE[SETTINGS['controlling']], entry['target_id']):
		judgement.untrack_target(LIFE[SETTINGS['controlling']], entry['target_id'])
	else:
		judgement.track_target(LIFE[SETTINGS['controlling']], entry['target_id'])
	
	create_tracking_menu()
