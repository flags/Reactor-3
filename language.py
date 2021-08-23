from globals import *

import alife

import logging
import random
import os

def prettify_string_array(array, max_length):
	"""Returns a human readable string from an array of strings."""
	_string = ''
	
	_i = 0
	for entry in array:
		if len(_string) > max_length:
			_string += ', and %s more.' % (_i+1)
			
			break
		
		if _i == 0:
			_string += entry
		elif 0<_i<len(array)-1:
			_string += ', %s' % entry
		elif _i == len(array)-1:
			_string += ' and %s.' % entry
		
		_i += 1
	
	return _string

def get_name(life):
	return ' '.join(life['name'])

def get_real_direction(direction, short=False):
	if abs(direction)<22 or abs(direction-360)<22:
		if short:
			return 'e'
		
		return 'east'
	elif abs(direction-45)<22:
		if short:
			return 'ne'
		
		return 'northeast'
	elif abs(direction-90)<22:
		if short:
			return 'n'
		
		return 'north'
	elif abs(direction-135)<22:
		if short:
			return 'nw'
		
		return 'northwest'
	elif abs(direction-180)<22:
		if short:
			return 'w'
		
		return 'west'
	elif abs(direction-225)<22:
		if short:
			return 'sw'
		
		return 'southwest'
	elif abs(direction-270)<22:
		if short:
			return 's'
		
		return 'south'
	elif abs(direction-315)<22:
		if short:
			return 'se'
		
		return 'southeast'
	else:
		if short:
			return 'e'
		
		return 'east'

def get_real_distance(distance):
	"""Returns the real-life representation of a distance."""
	
	if SETTINGS['distance unit'] == 'Yards':
		return distance*YARDS
	else:
		return distance*METERS

def get_real_distance_string(distance, round_up=False):
	_distance = get_real_distance(distance)
	_mods = ''
	
	if round_up:
		_distance = int(round(_distance))
	
	if not _distance == 1:
		_mods = 's'
	
	if SETTINGS['distance unit'] == 'Yards':
		return '%s yd%s' % (_distance, _mods)
	
	return '%s m%s' % (_distance, _mods)

def get_name_ownership(life, pronoun=False):
	if pronoun:
		if life['type'] == 'humanoid':
			return 'his'
		else:
			return 'its'
	
	return '%s\'s' % ' '.join(life['name'])

def get_introduction(life, posession=False):
	if 'player' in life:
		if posession:
			return 'Your'
		
		return 'You'
	
	if life['type'] == 'humanoid':
		if posession:
			return '%s\'s' % get_name(life)
		else:
			return get_name(life)
	else:
		#TODO: Check limb conditions
		if posession:
			return 'The %s\'s' % life['species']
		else:
			return 'The %s' % life['species']

def _load_strings(a, directory, filenames):
	for filename in [f for f in filenames if f.count('.txt')]:
		_map_name = filename.strip('.txt')
		TEXT_MAP[_map_name] = []
		
		with open(os.path.join(directory, filename), 'r') as e:
			TEXT_MAP[_map_name].extend([line.strip() for line in e.readlines()])

def load_strings():
	#TODO: Use better walk, like one in profiles.py
    for directory, _, filenames in os.walk("."):
        _load_strings(None, directory, filenames)

def load_dialog():
	with open(os.path.join(TEXT_DIR, 'dialog.txt')) as f:
		for line in f.readlines():
			line = line.rstrip()
			
			if not line or line.startswith('#'):
				continue
			
			try:
				_gist, _requirements, _text, _result = line.split(':')
			except:
				raise Exception('Error in dialog (wrong number of arguments): %s' % line)
			
			_dialog = {'gist': _gist,
			           'requirements': _requirements.split(','),
			           'text': _text,
			           'result': _result}
			
			if _gist in DIALOG_TOPICS:
				DIALOG_TOPICS[_gist].append(_dialog)
			else:
				DIALOG_TOPICS[_gist] = [_dialog]
	
	logging.debug('Loaded dialog.')

def generate_place_name():
	if not TEXT_MAP['places']:
		return 'Zoolandia %s' % WORLD_INFO['ticks']
	
	return TEXT_MAP['places'].pop(random.randint(0, len(TEXT_MAP['places'])-1))

def generate_scheme_title():
	return TEXT_MAP['nouns'][random.randint(0, len(TEXT_MAP['nouns'])-1)]

def generate_first_and_last_name_from_species(species):
	_map_first_names = '%s_first_names' % species
	_map_last_names = '%s_last_names' % species
	
	if not TEXT_MAP[_map_first_names] or not TEXT_MAP[_map_last_names]:
		return ('Wayne', 'Brady')
	
	_first_name = TEXT_MAP[_map_first_names].pop(random.randint(0, len(TEXT_MAP[_map_first_names])-1))
	_last_name = TEXT_MAP[_map_last_names].pop(random.randint(0, len(TEXT_MAP[_map_last_names])-1))
	
	return (_first_name, _last_name)

def format_injury(injury):
	if injury['lodged_item']:
		return 'a %s lodged in the %s' % (ITEMS[injury['lodged_item']]['name'], injury['limb'])
	elif injury['artery_ruptured']:
		return 'a ruptured artery in the %s' % injury['limb']
	elif injury['cut']:
		return 'a cut to the %s' % injury['limb']
	
	return 'nothing in particular.'

def generate_memory_phrase(memory):
	_details = [key for key in list(memory.keys()) if not key == 'text']
	_memory_age = WORLD_INFO['ticks']-memory['time_created']
	_topic = memory['text']
	
	if _topic == 'friendly':
		return '%s seems like a good guy.' % (' '.join(LIFE[memory['target']]['name']))
	else:
		print('DIDNT HAVE A PHRASE FOR',_topic)
