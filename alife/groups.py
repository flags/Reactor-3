from globals import *

import logging

def create_group(life):
	_group = {'creator': life['id'],
	    'leader': None,
	    'members': []}
	
	SETTINGS['groupid'] += 1
	GROUPS[SETTINGS['groupid']] = _group
	
	logging.debug('%s created group: %s' % (' '.join(life['name']), SETTINGS['groupid']-1))
	
def get_group(group_id):
	if not group_id in GROUPS:
		raise Exception('Group does not exist: %s' % group_id)
	
	return GROUPS[group_id]

def is_member(group_id, life_id):
	

def remove_member(group_id, life_id):
	_group = get_group(group_id)
	
	if 

def delete_group(life):
	for 