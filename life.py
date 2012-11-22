from globals import *
import logging
import copy
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

def initiate_limbs(body):
	for limb in body:
		#If canhold or canstore
		body[limb]['storing'] = []
		body[limb]['holding'] = []
		initiate_limbs(body[limb]['attached'])

def create_life(type,name=('Test','McChuckski')):
	if not type in LIFE_TYPES:
		raise Exception('Life type \'%s\' does not exist.' % type)
	
	#TODO: Any way to get rid of this call to `copy`?
	_life = copy.deepcopy(LIFE_TYPES[type])
	_life['name'] = name
	_life['speed'] = _life['speed_max']
	_life['path'] = []
	_life['flags'] = {}
	
	initiate_limbs(_life['body'])
	LIFE.append(_life)
	
	return _life

def set_state(life,flag,state):
	life['flags'][flag] = state

def get_state(life,flag):
	if flag in life['flags']:
		return life['flags'][flag]
	
	raise Exception('State \'%s\' does not exist.' % flag)

def tick(life):
	if life['speed']:
		life['speed'] -= 1
		return False
	else:
		life['speed'] = life['speed_max']
	
	print life['name'][0]

def show_life_info(life):
	for key in life:
		if key == 'body':
			continue
		
		print '%s: %s' % (key,life[key])
	
	return True

#Conductor
def tick_all_life():
	for life in LIFE:
		tick(life)
	
initiate_life('Human')
_life = create_life('Human',['derp','yerp'])
_life = create_life('Human',['nope','yerp'])
_life['speed'] = 50
_life['speed_max'] = 50
_life = create_life('Human',['zooom','yerp'])
_life['speed'] = 1
_life['speed_max'] = 1

for a in range(5000):
	tick_all_life()
#show_life_info(_life)
