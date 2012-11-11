from globals import *

def create_menu(position=[0,0],title='Untitled',padding=MENU_PADDING,callback=None,**kvargs):
	_menu = {'settings': {'position': list(position),'title': title, 'padding': padding},
		'callback': callback,
		'values':{}}
	_menu['menu'] = kvargs
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
			menu['values'][menu['values'].keys()[_key_index]] -= 1

def next_item(menu,index):
	_key = menu['menu'].keys()[index]
	
	if _key in menu['values'].keys():
		_key_index = menu['values'].keys().index(_key)
		
		if menu['values'][menu['values'].keys()[_key_index]] < len(menu['values'].keys()):
			menu['values'][menu['values'].keys()[_key_index]] += 1

def get_selected_item(menu,index):
	return (menu['menu'].keys()[index],menu['menu'].values()[index])

def run_callback(menu,index):
	if isinstance(menu['menu'].values()[index],list):
		key = menu['menu'].keys()[index]
		return menu['callback'](menu['menu'].values()[index][menu['values'][key]])
	
	return menu['callback'](menu['menu'].values()[index])