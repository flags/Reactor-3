from globals import *
import logging
import json

def load_item(item):
	with open(os.path.join(ITEM_DIR,item+'.json'),'r') as e:
		return json.loads(''.join(e.readlines()))

def initiate_item(name):
	if name in ITEM_TYPES:
		logging.warning('Item type \'%s\' is already loaded. Reloading...' % name)
	
	_item = load_item(name)
	
	if not 'icon' in _item:
		logging.warning('No icon set for item type \'%s\'. Using default (%s).' % (name,DEFAULT_ITEM_ICON))
		_item['tile'] = DEFAULT_ITEM_ICON
	
	if not 'flags' in _item:
		logging.error('No flags set for item type \'%s\'. Errors may occur.' % name)
	
	if 'attaches_to' in _item:
		_item['attaches_to'] = _item['attaches_to'].split('|')
	
	ITEM_TYPES[_item['name']] = _item
	
	return _item
