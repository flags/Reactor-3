from globals import *

import life as lfe

from . import camps
from . import brain

import logging

def camp_has_raid(camp_id):
	if camps.get_camp(camp_id)['raid']:
		return True
	
	return False

def create_raid(camp_id, raiders=[], join=None):
	_camp = camps.get_camp(camp_id)
	
	if not camp_has_raid(camp_id):
		_camp['raid'] = {'started': WORLD_INFO['ticks'],
		                 'raiders': [],
		                 'defenders': [],
		                 'score': 0}
		logging.debug('Created raid: %s' % _camp['name'])
	
	if join:
		defend_camp(camp_id, join)

def add_raiders(camp_id, raiders):
	_camp = camps.get_camp(camp_id)
	
	for raider in [r for r in raiders if not r in _camp['raid']['raiders']]:
		_camp['raid']['raiders'].append(raider)
		logging.debug('%s added to raid of camp %s' % (' '.join(LIFE[raider]['name']), _camp['name']))
		
		for defender in get_defenders(camp_id):
			if not brain.knows_alife_by_id(LIFE[defender], raider):
				if defender == raider:
					logging.warning('FIXME: Raider is member of camp.')
					continue
				
				brain.meet_alife(LIFE[defender], LIFE[raider])

def defend_camp(camp_id, life_id):
	_camp = camps.get_camp(camp_id)
	
	if not life_id in _camp['raid']['defenders']:
		_camp['raid']['defenders'].append(life_id)
		logging.debug('%s is now defending camp %s' % (' '.join(LIFE[life_id]['name']), _camp['name']))
	
	for raider in get_raiders(camp_id):
		if not brain.knows_alife_by_id(LIFE[life_id], raider):
			brain.meet_alife(LIFE[life_id], LIFE[raider])

def get_raiders(camp_id):
	return camps.get_camp(camp_id)['raid']['raiders']

def get_defenders(camp_id):
	return camps.get_camp(camp_id)['raid']['defenders']

def has_control(camp_id, group_id):
	if group_id == camps.get_controlling_group_global(camp_id):
		return True
	
	return False