from globals import *

import life as lfe

import camps

import logging

def camp_has_raid(camp_id):
	if camps.get_camp(camp_id)['raid']:
		return True
	
	return False

def create_raid(camp_id, raiders=[]):
	_camp = camps.get_camp(camp_id)
	
	if not camp_has_raid(camp_id):
		_camp['raid'] = {'started': WORLD_INFO['ticks'],
		                 'raiders': [],
		                 'score': 0}
		logging.debug('Created raid: %s' % _camp['name'])
	
	for raider in [r for r in raiders if not r in _camp['raid']['raiders']]:
		_camp['raid']['raiders'].append(raider)
		logging.debug('%s added to raid of camp %s' % (' '.join(LIFE[raider]['name']), _camp['name']))