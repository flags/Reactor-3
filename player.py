from globals import *
from alife import *

import libtcodpy as tcod
import graphics as gfx
import crafting
import weapons
import dialog
import menus
import items
import time
import life

import logging

def handle_input():
	global PLACING_TILE,RUNNING,SETTINGS,KEYBOARD_STRING

	if gfx.window_is_closed():
		SETTINGS['running'] = False
		
		return True
	
	if INPUT['\x1b'] or INPUT['q']:
		if ACTIVE_MENU['menu'] >= 0:
			menus.delete_menu(ACTIVE_MENU['menu'], abort=True)
		elif SETTINGS['controlling']['targeting']:
			SETTINGS['controlling']['targeting'] = None
			SETTINGS['controlling']['throwing'] = None
			SETTINGS['controlling']['firing'] = None
			SELECTED_TILES[0] = []
		elif SETTINGS['controlling']['actions']:
			life.clear_actions(SETTINGS['controlling'])
			
			if SETTINGS['controlling']['actions']:
				SETTINGS['controlling']['actions'] = []
		elif SETTINGS['controlling']['dialogs']:
			_dialog = [d for d in SETTINGS['controlling']['dialogs'] if d['enabled']]
			if _dialog:
				_dialog = _dialog[0]
				if not dialog.reset_dialog(_dialog):
					SETTINGS['controlling']['dialogs'] = []
		else:
			SETTINGS['running'] = False
	
	if INPUT['-']:
		if SETTINGS['draw console']:
			SETTINGS['draw console'] = False
		else:
			SETTINGS['draw console'] = True
	
	if SETTINGS['draw console']:
		return

	if INPUT['up']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.move_up(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['controlling']['targeting']:
			SETTINGS['controlling']['targeting'][1]-=1
		elif life.has_dialog(SETTINGS['controlling']):
			_dialog = [d for d in SETTINGS['controlling']['dialogs'] if d['enabled']][0]

			if _dialog['index']:
				_dialog['index'] -= 1
		else:
			life.clear_actions(SETTINGS['controlling'])
			life.add_action(SETTINGS['controlling'],{'action': 'move', 'to': (SETTINGS['controlling']['pos'][0],SETTINGS['controlling']['pos'][1]-1)},200)

	if INPUT['down']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.move_down(MENUS[ACTIVE_MENU['menu']], MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['controlling']['targeting']:
			SETTINGS['controlling']['targeting'][1]+=1
		elif life.has_dialog(SETTINGS['controlling']):
			_dialog = [d for d in SETTINGS['controlling']['dialogs'] if d['enabled']][0]
			
			if _dialog['index']<len(_dialog['topics'])-1:
				_dialog['index'] += 1
		else:
			life.clear_actions(SETTINGS['controlling'])
			life.add_action(SETTINGS['controlling'],{'action': 'move', 'to': (SETTINGS['controlling']['pos'][0],SETTINGS['controlling']['pos'][1]+1)},200)

	if INPUT['right']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.next_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['controlling']['targeting']:
			SETTINGS['controlling']['targeting'][0]+=1
		else:
			life.clear_actions(SETTINGS['controlling'])
			life.add_action(SETTINGS['controlling'],{'action': 'move', 'to': (SETTINGS['controlling']['pos'][0]+1,SETTINGS['controlling']['pos'][1])},200)

	if INPUT['left']:
		if not ACTIVE_MENU['menu'] == -1:
			menus.previous_item(MENUS[ACTIVE_MENU['menu']],MENUS[ACTIVE_MENU['menu']]['index'])
			menus.item_changed(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
		elif SETTINGS['controlling']['targeting']:
			SETTINGS['controlling']['targeting'][0]-=1
		else:
			life.clear_actions(SETTINGS['controlling'])
			life.add_action(SETTINGS['controlling'],{'action': 'move', 'to': (SETTINGS['controlling']['pos'][0]-1,SETTINGS['controlling']['pos'][1])},200)
	
	if INPUT['\r']:
		if SETTINGS['controlling'] and life.has_dialog(SETTINGS['controlling']):
			_dialog = [d for d in SETTINGS['controlling']['dialogs'] if d['enabled']][0]
			dialog.give_menu_response(SETTINGS['controlling'], _dialog)
			return False
		
		if ACTIVE_MENU['menu'] == -1:
			return False
		
		menus.item_selected(ACTIVE_MENU['menu'],MENUS[ACTIVE_MENU['menu']]['index'])
	
	if not SETTINGS['controlling']:
		return False
	
	if INPUT['?']:
		pix = tcod.image_from_console(0)
		tcod.image_save(pix, 'screenshot-%s.bmp' % time.time())
	
	if INPUT['P']:
		if SETTINGS['paused']:
			SETTINGS['paused'] = False
		else:
			SETTINGS['paused'] = True
	
	if INPUT['i']:
		if menus.get_menu_by_name('Inventory')>-1:
			menus.delete_menu(menus.get_menu_by_name('Inventory'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(SETTINGS['controlling'],check_hands=True)
		
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
		
		_inventory = life.get_fancy_inventory_menu_items(SETTINGS['controlling'],show_equipped=False,check_hands=False)
		
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
	
	if INPUT['E']:
		if menus.get_menu_by_name('Unequip')>-1:
			menus.delete_menu(menus.get_menu_by_name('Equip'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(SETTINGS['controlling'],show_equipped=True,check_hands=True,show_containers=False)
		
		if not _inventory:
			gfx.message('You have no items to unequip.')
			return False
		
		_i = menus.create_menu(title='Unequip',
			menu=_inventory,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k',
			on_select=inventory_unequip_action)
		
		menus.activate_menu(_i)
	
	if INPUT['c']:
		life.crouch(SETTINGS['controlling'])
	
	if INPUT['C']:
		life.stand(SETTINGS['controlling'])
	
	if INPUT['d']:
		if menus.get_menu_by_name('Drop')>-1:
			menus.delete_menu(menus.get_menu_by_name('Drop'))
			return False
		
		_inventory = life.get_fancy_inventory_menu_items(SETTINGS['controlling'],check_hands=True)
		
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
		
		if SETTINGS['controlling']['targeting']:
			life.throw_item(SETTINGS['controlling'],SETTINGS['controlling']['throwing']['id'],SETTINGS['controlling']['targeting'],1)
			SETTINGS['controlling']['targeting'] = None
			SELECTED_TILES[0] = []
			return True
		
		_throwable = life.get_fancy_inventory_menu_items(SETTINGS['controlling'],show_equipped=False,check_hands=True)
		
		if not _throwable:
			return False
		
		_i = menus.create_menu(title='Throw',
			menu=_throwable,
			padding=(1,1),
			position=(1,1),
			format_str='[$i] $k: $v',
			on_select=inventory_throw)
		
		menus.activate_menu(_i)
	
	if INPUT['v']:
		if menus.get_menu_by_name('Talk')>-1:
			menus.delete_menu(menus.get_menu_by_name('Talk'))
			return False
		
		if not SETTINGS['controlling']['targeting']:
			_menu_items = create_target_list()
	
			if not _menu_items:
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
				if entry['pos'] == SETTINGS['controlling']['targeting']:
					_target = entry
					break
			
			if not _target:
				gfx.message('There\'s nobody standing here!')
				return False
	
	if INPUT['V']:
		if SETTINGS['controlling']['dialogs']:
			_dialog = SETTINGS['controlling']['dialogs'].pop()
			SETTINGS['controlling']['dialogs'].append(dialog.create_dialog_with(SETTINGS['controlling'], _dialog['from'], _dialog))
			return True
		
		if not SETTINGS['controlling']['contexts']:
			return create_radio_menu()
		
		if SETTINGS['controlling']['encounters']:
			SETTINGS['following'] = SETTINGS['controlling']
			SETTINGS['controlling']['encounters'].pop(0)
		
		_i = menus.create_menu(title='React',
			menu=SETTINGS['controlling']['contexts'].pop()['items'],
			padding=(1,1),
			position=(1,1),
			format_str='$k: $v',
			on_select=life.react,
			on_close=life.avoid_react)
		
		menus.activate_menu(_i)
	
	if INPUT['f']:
		if menus.get_menu_by_name('Select Limb')>-1:
			return False
		
		if menus.get_menu_by_name('Aim at...')>-1:
			return False
			
		if menus.get_menu_by_name('Fire')>-1:
			menus.delete_menu(menus.get_menu_by_name('Fire'))
			return False
		
		if SETTINGS['controlling']['targeting']:
			if menus.get_menu_by_name('Select Target')>-1:
				return False
			
			_alife_menu = []
			for _life in life.get_all_life_at_position(life, SETTINGS['controlling']['targeting']):
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
				#print _alife_menu
				inventory_fire_select_limb(_alife_menu[0], no_delete=True)
			
			return True
		
		_weapons = []
		for hand in SETTINGS['controlling']['hands']:
			_limb = life.get_limb(SETTINGS['controlling'],hand)
			
			if not _limb['holding']:
				continue
			
			_item = life.get_inventory_item(SETTINGS['controlling'],_limb['holding'][0])
			
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
		
		#SETTINGS['controlling']['shoot_timer'] = SETTINGS['controlling']['shoot_timer_max']
		menus.activate_menu(_i)
	
	if INPUT['F']:
		if not SETTINGS['controlling']['encounters']:
			return False
		
		SETTINGS['following'] = SETTINGS['controlling']
		_target = SETTINGS['controlling']['encounters'].pop(0)['target']
		SETTINGS['controlling']['shoot_timer'] = 0
		
		speech.communicate(SETTINGS['controlling'], 'appear_friendly', matches=[{'id': _target['id']}])
		
		logging.debug('** APPEARING FRIENDLY **')
	
	if INPUT['H']:
		if not SETTINGS['controlling']['encounters']:
			return False
		
		SETTINGS['following'] = SETTINGS['controlling']
		_target = SETTINGS['controlling']['encounters'].pop(0)['target']
		SETTINGS['controlling']['shoot_timer'] = 0
		
		speech.communicate(SETTINGS['controlling'], 'appear_hostile', matches=[{'id': _target['id']}])
		
		logging.debug('** APPEARING HOSTILE **')
	
	if INPUT['r']:
		if menus.get_menu_by_name('Reload')>-1:
			menus.delete_menu(menus.get_menu_by_name('Reload'))
			return False
		
		_menu = []
		_loaded_weapons = []
		_unloaded_weapons = []
		_non_empty_ammo = []
		_empty_ammo = []
		
		for weapon in life.get_all_inventory_items(SETTINGS['controlling'],matches=[{'type': 'gun'}]):
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
		
		for ammo in life.get_all_inventory_items(SETTINGS['controlling'],matches=[{'type': 'magazine'},{'type': 'clip'}]):
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
	
	if INPUT['s']:
		if SETTINGS['controlling']['strafing']:
			SETTINGS['controlling']['strafing'] = False
			print 'Not strafing'
		else:
			SETTINGS['controlling']['strafing'] = True
			print 'Strafing'
	
	if INPUT['S']:
		if not SETTINGS['controlling']['encounters']:
			return False
		
		SETTINGS['following'] = SETTINGS['controlling']
		_target = SETTINGS['controlling']['encounters'].pop(0)['target']
		SETTINGS['controlling']['shoot_timer'] = 0
		
		speech.communicate(SETTINGS['controlling'], 'surrender', matches=[{'id': _target['id']}])
		
		logging.debug('** SURRENDERING **')
	
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
	
	if INPUT['O']:
		life.show_debug_info(SETTINGS['following'])
	
	if INPUT['Z']:
		life.crawl(SETTINGS['controlling'])
	
	if INPUT[',']:
		_items = items.get_items_at(SETTINGS['controlling']['pos'])
		
		if not _items:
			return False
		
		create_pick_up_item_menu(_items)
	
	if INPUT['a']:
		if menus.get_menu_by_name('Eat')>-1:
			menus.delete_menu(menus.get_menu_by_name('Eat'))
			return False
		
		_food = []
		for _item in life.get_all_inventory_items(SETTINGS['controlling'], matches=[{'type': 'food'}, {'type': 'drink'}]):
			_food.append(menus.create_item('single',
				items.get_name(_item),
				None,
				icon=_item['icon'],
				id=_item['id']))
		
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
	
	if INPUT['b']:
		#print SETTINGS['following']['actions']
		#print life.create_recent_history(SETTINGS['following'])
		life.print_life_table()
	
	if INPUT['y']:
		if LIFE.keys().index(SETTINGS['following']['id'])<len(LIFE.keys())-1:
			SETTINGS['following'] = LIFE[LIFE.keys().index(SETTINGS['following']['id'])+2]
			SETTINGS['controlling'] = LIFE[LIFE.keys().index(SETTINGS['controlling']['id'])+2]

	if INPUT['u']:
		if LIFE.keys().index(SETTINGS['following']['id'])>=1:
			SETTINGS['following'] = LIFE[LIFE.keys().index(SETTINGS['following']['id'])]
			SETTINGS['controlling'] = LIFE[LIFE.keys().index(SETTINGS['controlling']['id'])]

	if INPUT['l']:
		SUN_BRIGHTNESS[0] += 4
	
	if INPUT['k']:
		create_crafting_menu()

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
	
	_item = life.get_inventory_item(SETTINGS['controlling'],item)
	
	if _item['type'] == 'gun' and not life.can_hold_item(SETTINGS['controlling']):
		gfx.message('You can\'t possibly hold that!')
		
		return False
	
	life.add_action(SETTINGS['controlling'],{'action': 'equipitem',
		'item': item},
		200,
		delay=life.get_item_access_time(SETTINGS['controlling'],item))
	
	gfx.message('You start putting on the %s.' % _item['name'])
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_unequip(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['item']['id']
	
	_item = life.get_inventory_item(SETTINGS['controlling'],item)
	
	life.add_action(SETTINGS['controlling'],{'action': 'storeitem',
		'item': item,
		'container': entry['container']},
		200,
		delay=life.get_item_access_time(SETTINGS['controlling'],item))
	
	gfx.message('You begin storing %s.' % items.get_name(_item))
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_unequip_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = entry['id']
	
	_item = life.get_inventory_item(SETTINGS['controlling'],item)
	_menu = []
	
	for container in life.get_all_storage(SETTINGS['controlling']):		
		if container['capacity']+_item['size'] > container['max_capacity']:
			continue
		
		if container['id'] == item:
			continue
		
		_menu.append(menus.create_item('single',
			container['name'],
			'%s/%s' % (container['capacity'],container['max_capacity']),
			container=container['id'],
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
	item = entry['id']
	
	_name = items.get_name(life.get_inventory_item(SETTINGS['controlling'],item))
	
	life.add_action(SETTINGS['controlling'],{'action': 'dropitem',
		'item': item},
		200,
		delay=life.get_item_access_time(SETTINGS['controlling'],item))
	
	gfx.message('You start to drop %s.' % _name)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_eat(entry):
	key = entry['key']
	item = life.get_inventory_item(SETTINGS['controlling'], entry['id'])
	
	life.add_action(SETTINGS['controlling'],{'action': 'consumeitem',
		'item': item['id']},
		200,
		delay=life.get_item_access_time(SETTINGS['controlling'],item['id']))
	
	if item['type'] == 'food':
		gfx.message('You start to eat %s.' % items.get_name(item))
	else:
		gfx.message('You start to drink %s.' % items.get_name(item))
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_throw(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(SETTINGS['controlling'],entry['id'])
	
	_hand = life.is_holding(SETTINGS['controlling'],entry['id'])
	if _hand:
		SETTINGS['controlling']['targeting'] = SETTINGS['controlling']['pos'][:]
		SETTINGS['controlling']['throwing'] = item
		menus.delete_menu(ACTIVE_MENU['menu'])
		
		return True
	
	_hand = life.can_throw(SETTINGS['controlling'])
	if not _hand:
		gfx.message('Both of your hands are full.')
	
		menus.delete_menu(ACTIVE_MENU['menu'])
		return False

	_stored = life.item_is_stored(SETTINGS['controlling'],item['id'])
	if _stored:
		_delay = 40
		gfx.message('You start to remove %s from your %s.' % (item['name'],_stored['name']))
	else:
		_delay = 20
	
	SETTINGS['controlling']['throwing'] = item
	
	life.add_action(SETTINGS['controlling'],{'action': 'holditemthrow',
		'item': entry['id'],
		'hand': _hand},
		200,
		delay=_delay)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def target_view(entry):
	SETTINGS['following'] = LIFE[entry['target']]
	SETTINGS['controlling']['targeting'] = LIFE[entry['target']]['pos'][:]

def inventory_fire(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(SETTINGS['controlling'],entry['id'])
	
	menus.delete_menu(ACTIVE_MENU['menu'])
	
	SETTINGS['controlling']['firing'] = item
	
	if not life.is_holding(SETTINGS['controlling'],entry['id']):
		_hand = life.can_throw(SETTINGS['controlling'])
		if not _hand:
			gfx.message('Both of your hands are full.')
		
			menus.delete_menu(ACTIVE_MENU['menu'])
			return False
	
	_menu_items = create_target_list()
	
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
		_limbs.append(menus.create_item('single',
			limb,
			None,
			target=LIFE[entry['target']],
			limb=limb))
		
	_i = menus.create_menu(title='Select Limb',
		menu=_limbs,
		padding=(1,1),
		position=(1,1),
		on_select=inventory_fire_action,
	    on_close=exit_target,
		format_str='$k')
	
	menus.activate_menu(_i)

def inventory_fire_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	life.add_action(SETTINGS['controlling'],{'action': 'shoot',
	    'target': entry['target']['pos'][:],
	    'limb': entry['limb']},
		5000,
		delay=3)
	
	SETTINGS['controlling']['targeting'] = None
	SETTINGS['following'] = SETTINGS['controlling']
	SELECTED_TILES[0] = []
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def create_target_list():
	_menu_items = []
	for target in [l for l in LIFE.values() if sight.can_see_position(SETTINGS['controlling'], l['pos']) and not l == SETTINGS['controlling']]:
		if target['dead']:
			continue
		
		if not _menu_items:
			SETTINGS['following'] = target
		
		_menu_items.append(menus.create_item('single', target['name'], None, target=target['id']))
	
	return _menu_items

def create_dialog(entry):
	_target = entry['target']
	SETTINGS['controlling']['targeting'] = None
	SELECTED_TILES[0] = []
	
	_dialog = {'type': 'dialog',
          'from': SETTINGS['controlling']['id'],
          'enabled': True}
	SETTINGS['controlling']['dialogs'].append(dialog.create_dialog_with(SETTINGS['controlling'], _target, _dialog))
	menus.delete_active_menu()

def exit_target(entr):
	life.focus_on(SETTINGS['controlling'])
	SETTINGS['controlling']['targeting'] = None
	SELECTED_TILES[0] = []

def inventory_reload(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(SETTINGS['controlling'],entry['id'])
	
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
		for _weapon in life.get_held_items(SETTINGS['controlling'],matches=[{'type': 'gun','ammotype': item['ammotype'],'feed': item['type']}]):
			weapon = life.get_inventory_item(SETTINGS['controlling'],_weapon)
			
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
	item = life.get_inventory_item(SETTINGS['controlling'],entry['id'])
	
	if key == 'Remove feed':
		life.add_action(SETTINGS['controlling'],{'action': 'unload',
			'weapon': item},
			200,
			delay=20)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def inventory_handle_ammo(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	item = life.get_inventory_item(SETTINGS['controlling'],entry['id'])
	
	if key == 'Fill':
		if not item['id'] in life.get_held_items(SETTINGS['controlling']):
			if not life.can_hold_item(SETTINGS['controlling']):
				gfx.message('You need a hand free to fill the %s with %s rounds.' % (item['type'],item['ammotype']))
				return False
		
		life.add_action(SETTINGS['controlling'],{'action': 'removeandholditem',
			'item': item['id']},
			200,
			delay=20)
		
		gfx.message('You start filling the %s with %s rounds.' % (item['type'],item['ammotype']))
	
		_rounds = len(item['rounds'])
		for ammo in life.get_all_inventory_items(SETTINGS['controlling'],matches=[{'type': 'bullet', 'ammotype': item['ammotype']}]):
			life.add_action(SETTINGS['controlling'],{'action': 'refillammo',
				'ammo': item,
				'round': ammo},
				200,
				delay=20)
			
			_rounds += 1
			
			if _rounds>=item['maxrounds']:
				break
	else:
		life.add_action(SETTINGS['controlling'],{'action': 'reload',
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
	item = life.get_inventory_item(SETTINGS['controlling'],entry['id'])
	
	gfx.message('You start filling the %s with %s rounds.' % (item['type'],item['ammotype']))
	
	_rounds = len(item['rounds'])
	for ammo in life.get_all_inventory_items(SETTINGS['controlling'],matches=[{'type': 'bullet', 'ammotype': item['ammotype']}]):
		life.add_action(SETTINGS['controlling'],{'action': 'refillammo',
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
	_items = items.get_items_at(SETTINGS['controlling']['pos'])
	menus.delete_menu(ACTIVE_MENU['menu'])
	menus.delete_menu(ACTIVE_MENU['menu'])
	
	#TODO: Lowercase menu keys
	if entry['key'] == 'Equip':
		if entry['values'][entry['value']] == 'Wear':
			gfx.message('You start to pick up %s.' % items.get_name(entry['item']))
			
			life.add_action(SETTINGS['controlling'],{'action': 'pickupequipitem',
				'item': entry['item']},
				200,
				delay=life.get_item_access_time(SETTINGS['controlling'], entry['item']))
		
		elif entry['values'][entry['value']] in SETTINGS['controlling']['hands']:
			gfx.message('You start to pick up %s.' % items.get_name(entry['item']))
			
			life.add_action(SETTINGS['controlling'],{'action': 'pickupholditem',
				'item': entry['item'],
				'hand': entry['values'][entry['value']]},
				200,
				delay=life.get_item_access_time(SETTINGS['controlling'], entry['item']))
		
		return True
	
	gfx.message('You start to put %s in your %s.' %
		(items.get_name(entry['item']),entry['container']['name']))
	
	life.add_action(SETTINGS['controlling'],{'action': 'pickupitem',
		'item': entry['item'],
		'container': entry['container']},
		200,
		delay=life.get_item_access_time(SETTINGS['controlling'], entry['item']))
	
	return True

def pick_up_item_from_ground_action(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_item = items.get_item_from_uid(entry['item'])
	
	_menu = []
	#TODO: Can we equip this?
	_menu.append(menus.create_item('title','Actions',None,enabled=False))
	_menu.append(menus.create_item('single','Equip','Wear',item=_item))
	
	for hand in SETTINGS['controlling']['hands']:
		_menu.append(menus.create_item('single','Equip',hand,item=_item))
	
	_menu.append(menus.create_item('title','Store in...',None,enabled=False))
	for container in life.get_all_storage(SETTINGS['controlling']):		
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

def handle_options_menu(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	
	if key == 'Reload map':
		logging.warning('Map reloading is not well tested!')
		global MAP
		del MAP
		
		MAP = maps.load_map('map1.dat')
		
		logging.warning('Updating references to map. This may take a while.')
		for entry in [LIFE[i] for i in LIFE]:
			entry['map'] = MAP
		
		logging.warning('Redrawing LOS.')
		maps._render_los(MAP,PLAYER['pos'],cython=CYTHON_ENABLED)
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def radio_menu(entry):
	key = entry['key']
	value = entry['values'][entry['value']]
	_phrases = []
	
	if key == 'Distress':
		speech.announce(life, 'under_attack')
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def create_radio_menu():
	_phrases = []
	_phrases.append(menus.create_item('single', 'Distress', 'Radio for help.'))
	
	_menu = menus.create_menu(title='Radio',
		menu=_phrases,
		padding=(1,1),
		position=(1,1),
		format_str='$k: $v',
		on_select=radio_menu)
	
	menus.activate_menu(_menu)

def craft_menu_response(entry):
	key = entry['key']
	
	if entry['action'] == 'dismantle':
		crafting.dismantle_item(SETTINGS['controlling'], entry['item'])
	
	menus.delete_menu(ACTIVE_MENU['menu'])

def create_crafting_menu():
	_items = []
	for item in crafting.get_items_for_dismantle(SETTINGS['controlling']):
		_items.append(menus.create_item('single',
			item['name'],
			None,
			item=item['id'],
		    action='dismantle'))
	
	if _items:
		_items.insert(0, menus.create_item('title', 'Dismantle', None, enabled=False))
	else:
		gfx.message('You have no items to modify!')
		return False
	
	_menu = menus.create_menu(title='Crafting',
		menu=_items,
		padding=(1,1),
		position=(1,1),
		format_str='$k',
		on_select=craft_menu_response)
	
	menus.activate_menu(_menu)
	