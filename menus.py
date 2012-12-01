from globals import *

def create_menu(menu=[],position=[0,0],title='Untitled',format_str='$k: $v',padding=MENU_PADDING,on_select=None,on_change=None,dim=True):
	_menu = {'settings': {'position': list(position),'title': title,'padding': padding,'dim': dim,'format': format_str},
		'on_select': on_select,
		'on_change': on_change,
		'values':{}}
		
	#TODO: Does this need to be copied?
	_menu['menu'] = menu[:]
	_size = [0,len(_menu['menu'])+2+(_menu['settings']['padding'][1]*2)]
	
	#menuitem
	#type: single, list
	
	for entry in _menu['menu']:
		for value in entry['values']:
			_line = format_entry(_menu['settings']['format'],entry)
			
			if len(_line) > _size[0]:
				_size[0] = len(_line)
	
	_menu['settings']['size'] = (_size[0]+(_menu['settings']['padding'][0]*2),
		_size[1])
	_menu['settings']['console'] = console_new(_menu['settings']['size'][0],_menu['settings']['size'][1])
	
	MENUS.append(_menu)
	
	return MENUS.index(_menu)

def create_item(item_type,key,values,enabled=True):
	if not isinstance(values,list):
		values = [values]
	
	_item = {'type': item_type,
		'key': key,
		'enabled': enabled,
		'values': values,
		'value': 0}
	
	return _item

def format_entry(format_str,entry):
	return format_str.replace('$k', str(entry['key'])).replace('$v', str(entry['values'][entry['value']]))

def draw_menus():
	for menu in MENUS:
		_y_offset = menu['settings']['padding'][1]
		
		console_set_default_foreground(menu['settings']['console'],white)
		console_print(menu['settings']['console'],
			menu['settings']['padding'][0],
			_y_offset,
			menu['settings']['title'])
		
		_y_offset += 2
		for item in menu['menu']:
			if MENUS.index(menu) == ACTIVE_MENU['menu'] and menu['menu'].index(item) == ACTIVE_MENU['index'] and item['enabled']:
				#TODO: Colors
				console_set_default_foreground(menu['settings']['console'],white)
			elif not item['enabled']:
				console_set_default_foreground(menu['settings']['console'],darker_grey)
			elif menu['settings']['dim']:
				console_set_default_foreground(menu['settings']['console'],dark_grey)
			
			_line = format_entry(menu['settings']['format'],item)
			
			console_print(menu['settings']['console'],
				menu['settings']['padding'][0],
				_y_offset,
				_line)
			
			_y_offset += 1

def align_menus():
	for menu in MENUS:
		if not MENUS.index(menu):
			continue
		
		_prev_menu = MENUS[MENUS.index(menu)-1]
		_y_mod = _prev_menu['settings']['position'][1]+_prev_menu['settings']['size'][1]
		
		menu['settings']['position'][1] = _y_mod+1

def delete_menu(id):
	if ACTIVE_MENU['menu'] == id:
		ACTIVE_MENU['menu'] -= 1
		ACTIVE_MENU['index'] = 0
	
	MENUS.pop(id)

def get_menu(id):
	return MENUS[id]

def get_menu_by_name(name):
	for _menu in MENUS:
		if _menu['settings']['title'] == name:
			return MENUS.index(_menu)
	
	return -1

def activate_menu(id):
	ACTIVE_MENU['menu'] = id
	ACTIVE_MENU['index'] = 0

def activate_menu_by_name(name):
	ACTIVE_MENU['menu'] = get_menu_by_name(name)
	ACTIVE_MENU['index'] = 0

def previous_item(menu,index):
	if menu['menu'][index]['value']:
		menu['menu'][index]['value']-=1

def next_item(menu,index):
	if menu['menu'][index]['value']<len(menu['menu'][index]['values'])-1:
		menu['menu'][index]['value']+=1

def get_selected_item(menu,index):
	menu = get_menu(menu)
	_entry = menu['menu'][index]
	
	return (_entry['key'],_entry['values'][_entry['value']])

def item_selected(menu,index):
	_selected = get_selected_item(menu,index)
	menu = get_menu(menu)
	
	return menu['on_select'](_selected[0],_selected[1])
