from globals import *

def create_menu(**kvargs):
	if not kvargs.has_key('position'):
		kvargs['position'] = (0,0)
	
	_size = [0,len(kvargs)]
	
	for key in kvargs:
		_entry = '%s: %s' % (key,kvargs[key])
		if len(_entry) > _size[0]:
			_size[0] = len(_entry)
	
	kvargs['size'] = (_size[0]+(MENU_PADDING[0]*2),_size[1]+(MENU_PADDING[1]*2))
	kvargs['console'] = console_new(kvargs['size'][0],kvargs['size'][1])
	
	MENUS.append(kvargs)

create_menu(test='test here!')