from globals import *

import life as lfe

import judgement
import combat
import speech
import brain
import jobs

import logging

def create_group(life, add_creator=True):
	_group = {'creator': life['id'],
	    'leader': None,
	    'members': [],
	    'camp': None,
	    'time_created': WORLD_INFO['ticks'],
	    'last_updated': WORLD_INFO['ticks']}
	
	GROUPS[WORLD_INFO['groupid']] = _group
	
	lfe.memory(life, 'created group', group=WORLD_INFO['groupid'])
	logging.debug('%s created group: %s' % (' '.join(life['name']), WORLD_INFO['groupid']))
	
	if add_creator:
		add_member(WORLD_INFO['groupid'], life['id'])
		set_leader(WORLD_INFO['groupid'], life['id'])
	
	WORLD_INFO['groupid'] += 1

def get_group(group_id):
	if not group_id in GROUPS:
		raise Exception('Group does not exist: %s' % group_id)
	
	return GROUPS[group_id]

def add_member(group_id, life_id):
	if is_member(group_id, life_id):
		raise Exception('%s is already a member of group: %s' % (' '.join(LIFE[life_id]['name']), group_id))
	
	if LIFE[life_id]['group']:
		lfe.memory(LIFE[life_id], 'left group for group', left_group=LIFE[life_id]['group'], group=group_id)
		remove_member(LIFE[life_id]['group'], life_id)
	
	_group = get_group(group_id)
	for member in _group['members']:
		brain.meet_alife(LIFE[member], LIFE[life_id])
	
	LIFE[life_id]['group'] = group_id
	_group['members'].append(life_id)
	
	logging.debug('Added %s to group \'%s\'' % (' '.join(LIFE[life_id]['name']), WORLD_INFO['groupid']-1))

def remove_member(group_id, life_id):
	_group = get_group(group_id)
	
	if not is_member(group_id, life_id):
		raise Exception('%s is not a member of group: %s' % (' '.join(LIFE[life_id]['name']), group_id))
	
	_group['members'].remove(life_id)
	
	reconfigure_group(group_id)

def reconfigure_group(group_id):
	_group = get_group(group_id)
	
	if not _group['members']:
		delete_group(group_id)
		return False
	
	if not is_member(group_id, _group['leader']):
		logging.debug('Leader \'%s\' is leaving group #%s' % (' '.join(LIFE[_group['leader']]['name']), group_id))
	
	_successor = find_successor(group_id, assign=True)
	
	if _successor:
		logging.debug('\'%s\' is now leader of group #%s' % (' '.join(LIFE[_successor]['name']), group_id))
	else:
		logging.error('No successor could be found for group #%s (THIS SHOULD NOT HAPPEN)' % group_id)

def find_successor(group_id, assign=False):
	_group = get_group(group_id)
	_members = {l: 0 for l in _group['members']}
	
	for member1 in _group['members']:
		for member2 in _group['members']:
			if member1 == member2:
				continue
			
			_members[member2] += brain.knows_alife_by_id(LIFE[member1], member2)['trust']
	
	_highest = {'score': 0, 'id': None}
	for entry in _members:
		if not _highest['id'] or _members[entry] > _highest['score']:
			_highest['id'] = entry
			_highest['score'] = _members[entry]
	
	if _highest['id'] and assign:
		set_leader(group_id, _highest['id'])
	elif assign:
		raise Exception('No successor found, but `assign` is True. Stopping.')
	
	return _highest['id']

def assign_job(life, group_id, job):
	_group = get_group(life['group'])
	
	for member in _group['members']:
		jobs.add_job_candidate(job, LIFE[member])

def distribute(life, message, **kvargs):
	_group = get_group(life['group'])
	
	for member in _group['members']:
		speech.communicate(life, message, radio=True, matches=[{'id': member}], **kvargs)

def get_camp(group_id):
	return get_group(group_id)['camp']

def set_camp(group_id, camp_id):
	get_group(group_id)['camp'] = camp_id

def set_leader(group_id, life_id):
	get_group(group_id)['leader'] = life_id
	
	lfe.memory(LIFE[life_id], 'became leader of group', group=group_id)
	logging.debug('%s is now the leader of group #%s' % (' '.join(LIFE[life_id]['name']), group_id))

def get_combat_score(group_id, potential=False):
	_group = get_group(group_id)
	_score = 0
	
	for member in [LIFE[l] for l in _group['members']]:
		if combat.get_best_weapon(member):
			if not potential and not combat.weapon_equipped_and_ready(member):
				continue
			
			_score += 1
	
	return _score

def get_potential_combat_score(group_id):
	return get_combat_score(group_id, potential=True)

def get_status(group_id):
	_group = get_group(group_id)
	
	_total_trust = 0
	_total_danger = 0
	for member1 in _group['members']:
		for member2 in _group['members']:
			if member1 == member2:
				continue
			
			if not brain.knows_alife_by_id(LIFE[member1], member2):
				continue
			
			if judgement.can_trust(LIFE[member1], member2):
				_total_trust += judgement.get_trust(LIFE[member1], member2)
			else:
				_total_danger += LIFE[member1]['know'][member2]['danger']
	
	return _total_trust,_total_danger

def get_total_trust(group_id):
	return get_status(group_id)[0]

def get_total_danger(group_id):
	return get_status(group_id)[1]

def is_ready_to_camp(group_id):
	_group = get_group(group_id)
	
	if get_total_trust(group_id) < 4:
		return False
		
	if WORLD_INFO['ticks']-_group['last_updated'] >= len(_group['members'])*11:
		return True
	
	return False

def is_member(group_id, life_id):
	_group = get_group(group_id)
	
	if life_id in _group['members']:
		return True
	
	return False

def is_leader(group_id, life_id):
	_group = get_group(group_id)
	
	if life_id == _group['leader']:
		return True
	
	return False
	
def delete_group(group_id):
	for member in get_group(group_id)['members']:
		remove_member(group_id, member)
		LIFE[member]['group'] = None
		logging.warning('Forcing removal of member \'%s\' from non-empty group #%s.' % (' '.join(LIFE[member]['name']), group_id)) 
	
	logging.warning('Deleted group: %s' % group_id)
	
	del GROUPS[group_id]