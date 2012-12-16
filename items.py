from globals import *
import graphics as gfx
import logging
import json

def load_item(item):
	with open(os.path.join(ITEM_DIR,item+'.json'),'r') as e:
		return json.loads(''.join(e.readlines()))

def initiate_item(name):
	if name in ITEM_TYPES:
		logging.warning('Item type \'%s\' is already loaded. Reloading...' % name)
	
	item = load_item(name)
	
	if not 'prefix' in item:
		logging.warning('No prefix set for item type \'%s\'. Using default (%s).' % (name,DEFAULT_ITEM_PREFIX))
		item['prefix'] = DEFAULT_ITEM_PREFIX
	
	if not 'icon' in item:
		logging.warning('No icon set for item type \'%s\'. Using default (%s).' % (name,DEFAULT_ITEM_ICON))
		item['tile'] = DEFAULT_ITEM_ICON
	
	if not 'flags' in item:
		logging.error('No flags set for item type \'%s\'. Errors may occur.' % name)
		item['flags'] = ''
	
	if 'attaches_to' in item:
		item['attaches_to'] = item['attaches_to'].split('|')
	
	if 'capacity' in item:
		item['max_capacity'] = [int(c) for c in item['capacity'].split('x')]
		item['max_capacity'] = item['max_capacity'][0]*item['max_capacity'][1]
		item['capacity'] = 0
		item['storing'] = []
	
	if not 'size' in item:
		logging.warning('No size set for item type \'%s\'. Using default (%s).' % (name,DEFAULT_ITEM_SIZE))
		item['size'] = DEFAULT_ITEM_SIZE
	
	item['flags'] = item['flags'].split('|')
	
	item['size'] = 	[int(c) for c in item['size'].split('x')]
	item['size'] = item['size'][0]*item['size'][1]
	
	#Unicode isn't handled all that well on Windows for some reason...
	for key in item:
		_value = item[key]
		del item[key]
		item[str(key)] = _value
		
		if isinstance(item[key],unicode):
			item[key] = str(item[key])
	
	ITEM_TYPES[item['name']] = item
	
	return item

def create_item(name,position=[0,0,2]):
	item = ITEM_TYPES[name].copy()
	
	item['uid'] = len(ITEMS)
	item['pos'] = list(position)
	
	ITEMS[item['uid']] = item
	
	return item

def get_item_from_uid(uid):
	return ITEMS[uid]

def get_items_at(position):
	_items = []
	
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if item.has_key('id'):
			continue
		
		if item['pos'] == position:
			_items.append(item)
	
	return _items

def get_name(item):
	return '%s %s' % (item['prefix'],item['name'])

def draw_items():
	for _item in ITEMS:
		item = ITEMS[_item]
		
		if item.has_key('id'):
			continue
		
		if not item['pos'][2] <= CAMERA_POS[2]:
			continue
		
		if item['pos'][0] >= CAMERA_POS[0] and item['pos'][0] < CAMERA_POS[0]+MAP_WINDOW_SIZE[0] and\
			item['pos'][1] >= CAMERA_POS[1] and item['pos'][1] < CAMERA_POS[1]+MAP_WINDOW_SIZE[1]:
			_x = item['pos'][0] - CAMERA_POS[0]
			_y = item['pos'][1] - CAMERA_POS[1]
			gfx.blit_char(_x,_y,item['icon'],white,None)
