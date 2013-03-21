from globals import *

import references
import speech
import chunks

import logging

def find_nearest_unfounded_camp(life):
	_founded_camps = [CAMPS[camp]['reference'] for camp in CAMPS]
	_nearest_building = references.find_nearest_building(life, ignore_array=_founded_camps)
	
	return _nearest_building['reference']

def found_camp(life, reference, announce=False):
	_camp = {'id': len(CAMPS),
		'reference': reference,
		'founder': life['id'],
		'time_founded': WORLD_INFO['ticks']}
	
	CAMPS[_camp['id']] = _camp 
	logging.debug('%s founded camp #%s.' % (' '.join(life['name']), _camp['id']))
	discover_camp(life, _camp)
	speech.announce(life, 'share_camp_info', camp=_camp)

def unfound_camp(life, camp):
	pass

def get_all_alife_in_camp(life, camp):
	#TODO: We should write a function to do this for references, then filter the results here
	#TODO: Can we just add a is_member funtion?
	pass

def has_discovered_camp(life, camp):
	if camp['id'] in life['known_camps']:
		return True
	
	return False

def discover_camp(life, camp):
	life['known_camps'][camp['id']] = camp
	life['known_camps'][camp['id']]['time_discovered'] = WORLD_INFO['ticks']

	if not camp['founder'] == life['id']:
		logging.debug('%s discovered camp #%s.' % (' '.join(life['name']), camp['id']))

def is_in_camp(life, camp):
	for chunk_key in camp['reference']:
		_chunk_pos = chunks.get_chunk(chunk_key)
		
		print _chunk_pos
