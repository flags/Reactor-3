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
	
	return _menu

def previous_item(menu,index):
	_key = menu['menu'].keys()[index]
	
	if _key in menu['values'].keys():
		_key_index = menu['values'].keys().index(_key)
		
		if menu['values'][menu['values'].keys()[_key_index]]:
			key = menu['menu'].keys()[index]
			menu['values'][menu['values'].keys()[_key_index]] -= 1
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
			menu['on_change'](_key,menu['menu'].values()[index][menu['values'][key]])
			return True
	
	return False

def get_selected_item(menu,index):
	return (menu['menu'].keys()[index],menu['menu'].values()[index])

def item_selected(menu,index):
	if isinstance(menu['menu'].values()[index],list):
		key = menu['menu'].keys()[index]
		return menu['on_select'](menu['menu'].values()[index][menu['values'][key]])
	
	return menu['on_select'](menu['menu'].values()[index])

def menu_exists(name):
	for _menu in MENUS:
		if _menu['settings']['title'] == name:
			return True
	
	return False
