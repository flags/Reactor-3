from globals import *

import profiles
import items

import logging
import json

import os

def _capsule():
	return {'uid': None,
	        'date': WORLD_INFO['ticks'],
	        '_on_disk': False,
	        '_allow_dump': False}

def _write_to_cache(cache_name, data):
	with open(os.path.join(profiles.get_world_directory(WORLD_INFO['id']), '%s_history.dat' % cache_name), 'a') as f:
		f.write(json.dumps(data)+'\n\n')

def _read_from_cache(cache_name, uid):
	with open(os.path.join(profiles.get_world_directory(WORLD_INFO['id']), '%s_history.dat' % cache_name)) as f:
		for item in [json.loads(s) for s in f]:
			if item['uid'] == uid:
				item['_on_disk'] = False
				item['date'] = WORLD_INFO['ticks']
				ITEMS_HISTORY[item['uid']].update(item)

				logging.debug('Cache: Loaded item %s from cache.' % uid)
				return item

def save_cache(cache_name):
	_path = os.path.join(profiles.get_world_directory(WORLD_INFO['id']), '%s_history.dat' % cache_name)
	_write_cache = []

	if not os.path.exists(_path):
		return False

	with open(_path, 'r') as f:
		_cache = f.readlines()

		for _line in _cache:
			line = _line.rstrip()
			
			if line == '\n' or not line:
				continue
			
			_historic_item = json.loads(line)
			
			if not _historic_item['_allow_dump']:
				continue
			
			_dump_string = json.dumps(_historic_item)
			
			_write_cache.append(_dump_string)

	with open(_path, 'w') as f:
		f.write('\n'.join(_write_cache))

	logging.debug('Cache: Saved to disk.')

def commit_cache(cache_name):
	_path = os.path.join(profiles.get_world_directory(WORLD_INFO['id']), '%s_history.dat' % cache_name)
	_write_cache = []

	if not os.path.exists(_path):
		return False

	with open(_path, 'r') as f:
		_cache = f.readlines()

		for _line in _cache:
			line = _line.strip()
			
			if line == '\n' or not line:
				continue
			
			print repr(line)
			_historic_item = json.loads(line)
			_historic_item['_allow_dump'] = True
			_write_cache.append(json.dumps(_historic_item))

	if cache_name == 'items':
		for item_uid in ITEMS_HISTORY:
			_historic_item = ITEMS_HISTORY[item_uid]
			if not _historic_item['_on_disk']:
				continue
			
			_historic_item['_allow_dump'] = True

	with open(_path, 'w') as f:
		f.write('\n'.join(_write_cache))

	logging.debug('Cache: Committed.')

def scan_cache():
	for item_uid in ITEMS_HISTORY:
		_historic_item = ITEMS_HISTORY[item_uid]

		if _historic_item['_on_disk']:
			continue

		if WORLD_INFO['ticks']-_historic_item['date']>=100:
			logging.debug('Cache: Moved item %s to disk' % item_uid)
			_historic_item['_on_disk'] = True
			_write_to_cache('items', _historic_item)

			if 'item' in _historic_item:
				del _historic_item['item']

def offload_item(raw_item):
	_item = _capsule()
	items.clean_item_for_save(raw_item)
	_item['uid'] = raw_item['uid']
	_item['item'] = raw_item

	ITEMS_HISTORY[_item['uid']] = _item

	logging.debug('Cache: Offloaded item (in memory)')

def retrieve_item(item_uid):
	_historic_item = ITEMS_HISTORY[item_uid]

	if _historic_item['_on_disk']:
		raise Exception('Ahhhhhhhhhhhh')
		#TODO: Grab from disk
		pass

	return _historic_item['item']