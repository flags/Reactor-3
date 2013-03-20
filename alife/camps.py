from globals import *

import references
import speech

import logging

def find_nearest_unfounded_camp(life):
	_nearest_building = references.find_nearest_building(life)
	return _nearest_building	

def found_camp(life, reference, announce=False):
	_camp = {'id': len(CAMPS),
		'reference': reference,
		'founder': life['id'],
		'time_founded': WORLD_INFO['ticks']}
	
	CAMPS[_camp['id']] = _camp 
	#speech.announce(life, 'founded_camp', reference=reference)
	logging.debug('%s founded camp #%s.' % (' '.join(life['name']), _camp['id']))
	discover_camp(life, _camp)

def unfound_camp(life, camp):
	pass

def get_all_alife_in_camp(life, camp):
	#TODO: We should write a function to do this for references, then filter the results here
	pass

def has_discovered_camp(life, camp):
	if camp['id'] in life['known_camps']:
		return True
	
	return False

def discover_camp(life, camp):
	life['known_camps'][camp['id']] = camp
	life['known_camps'][camp['id']]['time_discovered'] = WORLD_INFO['ticks']

	logging.debug('%s discovered camp #%s.' % (' '.join(life['name']), camp['id']))
