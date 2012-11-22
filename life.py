from globals import *
import logging
import json
import os

def load_life(life):
	with open(os.path.join(LIFE_DIR,life+'.json'),'r') as e:
		return json.loads(e.readline())

def calculate_base_stats(life):
	stats = {'arms': None,
		'legs': None,
		'melee': None,
		'speed_max': LIFE_MAX_SPEED}
	race_type = None
	
	_flags = life['flags'].split('|')
	
	for flag in _flags:
		if _flags.index(flag) == 0:
			race_type = flag
		
		elif flag.count('LEGS'):
			stats['legs'] = flag.partition('[')[2].partition(']')[0].split(',')
		
		elif flag.count('ARMS'):
			stats['arms'] = flag.partition('[')[2].partition(']')[0].split(',')
		
		elif flag.count('MELEE'):
			stats['melee'] = flag.partition('[')[2].partition(']')[0].split(',')
	
	stats['speed_max'] = LIFE_MAX_SPEED-(len(stats['legs'])*10)
	
	return stats

def initiate_life(name):
	if name in LIFE_TYPES:
		logging.warning('Life type \'%s\' is already loaded. Reloading...' % name)
	
	_life = load_life(name)
	
	if not 'icon' in _life:
		logging.warning('No icon set for life type \'%s\'. Using default (%s).' % (name,DEFAULT_ICON))
		_life['tile'] = DEFAULT_ICON
	
	if not 'flags' in _life:
		logging.error('No flags set for life type \'%s\'. Errors may occur.' % name)
	
	_life.update(calculate_base_stats(_life))
	
	LIFE_TYPES[name] = _life
	
	return _life

def show_life_info(name):
	if name in LIFE_TYPES:
		for key in LIFE_TYPES[name]:
			if key == 'body':
				continue
			
			print '%s: %s' % (key,LIFE_TYPES[name][key])
		
		return True
	
	raise Exception('Could not find life type \'%s\'.' % name)
	
initiate_life('Human')
show_life_info('Human')
