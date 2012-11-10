from globals import *

def create_menu(position=(0,0),title='Untitled',padding=MENU_PADDING,callback=None,**kvargs):
	_menu = {'settings': {'position': position,'title': title, 'padding': padding},
		'callback': callback}
	_menu['menu'] = kvargs
	_size = [0,len(_menu['menu'])+2+(_menu['settings']['padding'][1]*2)]
	
	for key in _menu['menu']:
		_entry = '%s: %s' % (key,_menu['menu'][key])
		if len(_entry) > _size[0]:
			_size[0] = len(_entry)
	
	_menu['settings']['size'] = (_size[0]+(_menu['settings']['padding'][0]*2),
		_size[1])
	_menu['settings']['console'] = console_new(_menu['settings']['size'][0],_menu['settings']['size'][1])
	
	MENUS.append(_menu)

def get_selected_item(menu,index):
	return menu['callback'](menu['menu'].values()[index])