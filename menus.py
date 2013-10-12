from globals import *

import libtcodpy as tcod

def create_menu(menu=[],position=[0,0], title='Untitled', format_str='$k: $v', padding=MENU_PADDING,
                on_select=None, on_change=None, on_close=None, on_move=None, dim=True, alignment='', action=None):
	_menu = {'settings': {'position': list(position),'title': title,'padding': padding,'dim': dim,'format': format_str},
		'on_select': on_select,
		'on_change': on_change,
	    'on_move': on_move,
		'on_close': on_close,
		'alignment': alignment,
		'index': 0,
		'values':{},
		'action':action}
		
	#TODO: Does this need to be copied?
	_menu['menu'] = menu[:]
	_size = [len(title),len(_menu['menu'])+2+(_menu['settings']['padding'][1]*2)]
	
	_uid = 0
	for entry in _menu['menu']:
		entry['uid'] = _uid
		_uid+=1
		
		for value in entry['values']:
			_line = format_entry(_menu['settings']['format'],entry)
			
			if len(_line) > _size[0]:
				_size[0] = len(_line)
	
	_menu['settings']['size'] = (_size[0]+(_menu['settings']['padding'][0]*2),_size[1])
	_menu['settings']['console'] = tcod.console_new(_menu['settings']['size'][0],_menu['settings']['size'][1])
	
	MENUS.append(_menu)
	
	return MENUS.index(_menu)

def create_item(item_type,key,values,icon=' ',enabled=True, color=(tcod.gray, tcod.white), **kwargs):
	if not isinstance(values,list):
		values = [values]
	
	_item = {'type': item_type,
		'key': key,
		'enabled': enabled,
		'icon': icon,
		'color': color,
		'values': values,
		'value': 0}
	
	if _item['type'] in ['title','spacer']:
		_item['enabled'] = False
	
	_item.update(kwargs)
	
	return _item

def remove_item_from_menus(matching):
	for menu in MENUS:
		for item in menu['menu'][:]:
			_match = True
			
			for key in matching:
				#print item.keys()
				if not key in item or not matching[key] == item[key]:
					_match = False
					break
			
			if _match:
				menu['menu'].remove(item)

def format_entry(format_str,entry):
	return format_str.replace('$k', str(entry['key']))\
		.replace('$v', str(entry['values'][entry['value']]))\
		.replace('$i', str(entry['icon']))

def redraw_menu(menu):
	tcod.console_clear(menu['settings']['console'])

def draw_menus():
	for menu in MENUS:
		_y_offset = menu['settings']['padding'][1]
		
		tcod.console_set_default_foreground(menu['settings']['console'], tcod.white)
		tcod.console_print(menu['settings']['console'],
			menu['settings']['padding'][0],
			_y_offset,
			menu['settings']['title'])
		
		_y_offset += 2		
		
		for item in menu['menu']:
			if item['type'] == 'title':
				tcod.console_set_default_foreground(menu['settings']['console'], tcod.white)
				_line = format_entry('- $k',item)
			elif item['type'] == 'spacer':
				tcod.console_set_default_foreground(menu['settings']['console'], tcod.white)
				_line = item['key']*(menu['settings']['size'][0]-menu['settings']['padding'][0])
			elif item['type'] == 'input':
				#TODO: Input check?
				if MENUS.index(menu) == ACTIVE_MENU['menu'] and menu['menu'].index(item) == menu['index'] and item['enabled']:
					#TODO: Colors
					tcod.console_set_default_foreground(menu['settings']['console'], item['color'][1])
				elif not item['enabled']:
					tcod.console_set_default_foreground(menu['settings']['console'], tcod.dark_sepia)
				elif menu['settings']['dim']:
					tcod.console_set_default_foreground(menu['settings']['console'], item['color'][0])
				
				_line = format_entry(menu['settings']['format'],item)
			else:
				if MENUS.index(menu) == ACTIVE_MENU['menu'] and menu['menu'].index(item) == menu['index'] and item['enabled']:
					#TODO: Colors
					tcod.console_set_default_foreground(menu['settings']['console'], item['color'][1])
				elif not item['enabled']:
					tcod.console_set_default_foreground(menu['settings']['console'], tcod.dark_sepia)
				elif menu['settings']['dim']:
					tcod.console_set_default_foreground(menu['settings']['console'], item['color'][0])
			
				#TODO: Per-item formats here
				_line = format_entry(menu['settings']['format'],item)
			
			tcod.console_print(menu['settings']['console'],
				menu['settings']['padding'][0],
				_y_offset,
				_line)
			
			_y_offset += 1

def align_menus():
	for menu in MENUS:
		if not MENUS.index(menu):
			continue
		
		if not menu['alignment'] and menu['settings']['position'][1] > 1:
			continue
		
		if not 'position_mod' in menu['settings']:
			menu['settings']['position_mod'] = menu['settings']['position'][:]
		
		if menu['alignment'] == 'botleft':
			menu['settings']['position'][0] = 1
			menu['settings']['position'][1] = WINDOW_SIZE[1]-menu['settings']['size'][1]-1
		
		if menu['alignment']:
			menu['settings']['position'][0] += menu['settings']['position_mod'][0]
			menu['settings']['position'][1] += menu['settings']['position_mod'][1]
			continue
		
		_prev_menu = MENUS[MENUS.index(menu)-1]
		_y_mod = _prev_menu['settings']['position'][1]+_prev_menu['settings']['size'][1]
		
		menu['settings']['position'][1] = _y_mod+1

def delete_menu(id, abort=False):
	_menu = get_menu(id)
	
	if _menu['on_close'] and abort:
		_entry = get_selected_item(id, _menu['index'])
		_menu['on_close'](_entry)
	
	if ACTIVE_MENU['menu'] == id:
		ACTIVE_MENU['menu'] -= 1
	
	MENUS.pop(id)

def delete_active_menu(abort=True):
	if MENUS:
		delete_menu(ACTIVE_MENU['menu'], abort=abort)

def get_menu(id):
	return MENUS[id]

def get_menu_by_name(name):
	for _menu in MENUS:
		if _menu['settings']['title'] == name:
			return MENUS.index(_menu)
	
	return -1

def activate_menu(id):
	ACTIVE_MENU['menu'] = id
	MENUS[id]['index'] = find_item_after(MENUS[id])
	
	if MENUS[id]['on_move']:
		_entry = get_selected_item(id, MENUS[id]['index'])
		return MENUS[id]['on_move'](_entry)

def activate_menu_by_name(name):
	ACTIVE_MENU['menu'] = get_menu_by_name(name)

def find_item_before(menu,index=0):
	_items = menu['menu'][:index][:]
	_items.reverse()
	
	for item in _items:
		if item['enabled']:
			return menu['menu'].index(item)
	
	return find_item_before(menu,index=len(menu['menu']))

def find_item_after(menu,index=-1):
	for item in menu['menu'][index+1:]:
		if item['enabled']:
			return menu['menu'].index(item)
	
	return find_item_after(menu)

def get_menu_index_by_key(menu, key):
	menu = get_menu(menu)
	
	_i = 0
	for entry in menu['menu']:
		if entry['key'] == key:
			return _i
		
		_i += 1
	
	return -1

def get_menu_index_by_flag(menu, flag, value):
	menu = get_menu(menu)
	
	_i = 0
	for entry in menu['menu']:
		if entry[flag] == value:
			return _i
		
		_i += 1
	
	return -1

def go_to_menu_index(menu, index):
	get_menu(menu)['index'] = index
	
	if get_menu(menu)['on_move']:
		_entry = get_selected_item(menu, index)
		return get_menu(menu)['on_move'](_entry)

def move_up(menu, index):
	menu['index'] = find_item_before(menu, index=index)
	
	if menu['on_move']:
		_entry = get_selected_item(MENUS.index(menu), menu['index'])
		return menu['on_move'](_entry)

def move_down(menu, index):
	menu['index'] = find_item_after(menu, index=index)
	
	if menu['on_move']:
		_entry = get_selected_item(MENUS.index(menu), menu['index'])
		return menu['on_move'](_entry)

def previous_item(menu,index):
	if menu['menu'][index]['value']:
		menu['menu'][index]['value']-=1
		redraw_menu(menu)

def next_item(menu,index):
	if menu['menu'][index]['value']<len(menu['menu'][index]['values'])-1:
		menu['menu'][index]['value']+=1
		redraw_menu(menu)

def get_selected_item(menu,index):
	menu = get_menu(menu)
	_entry = menu['menu'][index]
	
	return _entry

def item_selected(menu,index):
	_entry = get_selected_item(menu,index)
	menu = get_menu(menu)
	
	if menu['on_select']:
		return menu['on_select'](_entry)
	
	return False

def item_changed(menu,index):
	_entry = get_selected_item(menu,index)
	menu = get_menu(menu)
	
	if menu['on_change']:
		return menu['on_change'](_entry)
	else:
		return False
	
def is_getting_input(menu_id):
	_item = get_selected_item(menu_id, MENUS[menu_id]['index'])
		
	if _item['type'] == 'input':
		return _item
	
	return False

def is_any_menu_getting_input():
	for menu_id in [MENUS.index(m) for m in MENUS]:
		_item = is_getting_input(menu_id)
		
		if _item:
			return _item
	
	return False
