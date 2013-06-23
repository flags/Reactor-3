from globals import *

import logging

def create_group(life, add_creator=True):
	_group = {'creator': life['id'],
	    'leader': None,
	    'members': []}
	
	SETTINGS['groupid'] += 1
	GROUPS[SETTINGS['groupid']] = _group
	
	logging.debug('%s created group: %s' % (' '.join(life['name']), SETTINGS['groupid']))
	
	if add_creator:
		add_member(SETTINGS['groupid'], life['id'])

def add_member(group_id, life_id):
	if is_member(group_id, life_id):
		raise Exception('%s is already a member of group: %s' % (' '.join(LIFE[life_id]['name']), group_id))
	
	LIFE[life_id]['group'] = group_id
	get_group(group_id)['members'].append(life_id)
	
	logging.debug('Added %s to group \'%s\'' % (' '.join(LIFE[life_id]['name']), SETTINGS['groupid']-1))

def get_group(group_id):
	if not group_id in GROUPS:
		raise Exception('Group does not exist: %s' % group_id)
	
	return GROUPS[group_id]

def is_member(group_id, life_id):
	_group = get_group(group_id)
	
	if life_id in _group['members']:
		return True
	
	return False

def remove_member(group_id, life_id):
	_group = get_group(group_id)
	
	if not is_member(group_id, life_id):
		raise Exception('%s is not a member of group: %s' % (' '.join(LIFE[life_id]), group_id))
	
def delete_group(group_id):
	for member in get_group(group_id)['members']:
		pass