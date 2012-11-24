from globals import *

def create_menu(menu={},position=[0,0],title='Untitled',padding=MENU_PADDING,on_select=None,on_change=None,dim=True):
	_menu = {'settings': {'position': list(position),'title': title,'padding': padding,'dim': dim},
		'on_select': on_select,
		'on_change': on_change,
		'values':{}}
	_menu['menu'] = menu
	_size = [0,len(_menu['menu'])+2+(_menu['settings']['padding'][1]*2)]
	
	for key in _menu['menu']:
		if isinstance(_menu['menu'][key],list):
			for i in range(len(_menu['menu'][key])):
				_entry = '%s: %s' % (key,_menu['menu'][key][0])
				
				if len(_entry) > _size[0]:
					_size[0] = len(_entry)
			
			_menu['values'][key] = 0
		else:
			_entry = '%s: %s' % (key,_menu['menu'][key])
		
			if len(_entry) > _size[0]:
				_size[0] = len(_entry)
	
	_menu['settings']['size'] = (_size[0]+(_menu['settings']['padding'][0]*2),
		_size[1])
	_menu['settings']['console'] = console_new(_menu['settings']['size'][0],_menu['settings']['size'][1])
	
	MENUS.append(_menu)
	
	return MENUS.index(_menu)

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
	_key = menu['menu'].keys()[index]
	
	if _key in menu['values'].keys():
		_key_index = menu['values'].keys().index(_key)
		
		if menu['values'][menu['values'].keys()[_key_index]]:
			key = menu['menu'].keys()[index]
			menu['values'][menu['values'].keys()[_key_index]] -= 1
			if menu['on_change']:
				menu['on_change'](_key,menu['menu'].values()[index][menu['values'][key]])
			return True
	
	return False

def next_item(menu,index):
	_key = menu['menu'].keys()[index]
	
	if _key in menu['values'].keys():
		_key_index = menu['values'].keys().index(_key)
		
		if menu['values'][menu['values'].keys()[_key_index]] < len(menu['values'].keys()):
			key = menu['menu'].keys()[index]
			menu['values'][menu['values'].keys()[_key_index]] += 1
			if menu['on_change']:
				menu['on_change'](_key,menu['menu'].values()[index][menu['values'][key]])
			return True
	
	return False

def get_selected_item(menu,index):
	return (menu['menu'].keys()[index],menu['menu'].values()[index])

def item_selected(menu,index):
	menu = get_menu(menu)
	
	if isinstance(menu['menu'].values()[index],list):
		key = menu['menu'].keys()[index]
		return menu['on_select'](key,menu['menu'].values()[index][menu['values'][key]])
	
	return menu['on_select'](menu['menu'].keys()[index],menu['menu'].values()[index])
