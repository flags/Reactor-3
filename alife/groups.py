from globals import *

import graphics as gfx
import life as lfe

import judgement
import movement
import action
import combat
import speech
import events
import chunks
import camps
import brain
import stats
import raids
import jobs

import logging

def create_group(life, add_creator=True):
	_group = {'creator': life['id'],
	    'leader': None,
	    'members': [],
	    'shelter': None,
	    'events': {},
	    'event_id': 1,
	    'announce_event': None,
	    'time_created': WORLD_INFO['ticks'],
	    'last_updated': WORLD_INFO['ticks'],
	    'flags': {},
	    'claimed_motive': 'survival',
	    'actual_motive': 'survival',
	    'stats': {'kills': 0, 'murders': 0}}
	
	WORLD_INFO['groups'][str(WORLD_INFO['groupid'])] = _group
	
	lfe.memory(life, 'created group', group=str(WORLD_INFO['groupid']))
	logging.debug('%s created group: %s' % (' '.join(life['name']), WORLD_INFO['groupid']))
	
	if add_creator:
		add_member(str(WORLD_INFO['groupid']), life['id'])
		set_leader(str(WORLD_INFO['groupid']), life['id'])
	
	WORLD_INFO['groupid'] += 1
	
	return str(WORLD_INFO['groupid']-1)

def get_group(group_id):
	if not group_id in WORLD_INFO['groups']:
		raise Exception('Group does not exist: %s' % group_id)
	
	return WORLD_INFO['groups'][group_id]

def flag(group_id, flag, value):
	get_group(group_id)['flags'][flag] = value

def get_flag(group_id, flag):
	if not flag in get_group(group_id)['flags']:
		return None
	
	return get_group(group_id)['flags'][flag]

def discover_group(life, group_id):
	if not group_id in life['known_groups']:
		life['known_groups'].append(group_id)
		
		if 'player' in life:
			gfx.message('You learn about group %s.' % group_id)
		return True
	
	return False

def get_group_relationships():
	_groups = {grp: {_grp: 0 for _grp in WORLD_INFO['groups'] if not _grp == grp} for grp in WORLD_INFO['groups']}
	
	#for grp in _groups:
	#	print _groups[grp]

def add_member(group_id, life_id):
	if is_member(group_id, life_id):
		raise Exception('%s is already a member of group: %s' % (' '.join(LIFE[life_id]['name']), group_id))
	
	if LIFE[life_id]['group']:
		lfe.memory(LIFE[life_id], 'left group for group', left_group=LIFE[life_id]['group'], group=group_id)
		remove_member(LIFE[life_id]['group'], life_id)
	
	_group = get_group(group_id)
	for member in _group['members']:
		brain.meet_alife(LIFE[member], LIFE[life_id])
	
	if _group['shelter']:
		LIFE[life_id]['shelter'] = _group['shelter']
		lfe.memory(LIFE[life_id], 'shelter founder', shelter=_group['shelter'], founder=_group['leader'])
	
	discover_group(LIFE[life_id], group_id)
	LIFE[life_id]['group'] = group_id
	_group['members'].append(life_id)
	
	if _group['leader'] and 'player' in LIFE[_group['leader']]:
		gfx.message('%s has joined your group.' % ' '.join(LIFE[life_id]['name']), style='good')
	
	if SETTINGS['controlling'] == life_id:
		gfx.message('You join group %s.' % group_id, style='good')
	
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
	_group = get_group(group_id)
	
	for member in _group['members']:
		jobs.add_job_candidate(job, LIFE[member])

def distribute(life, message, filter_by=[], **kvargs):
	_group = get_group(life['group'])
	
	for member in _group['members']:
		if member in filter_by:
			continue
		
		speech.communicate(life, message, radio=True, matches=[{'id': member}], **kvargs)

def add_event(group_id, event):
	_group = get_group(group_id)
	
	_group['events'][str(_group['event_id'])] = event
	_group['event_id'] += 1
	
	return str(_group['event_id']-1)

def get_event(group_id, event_id):
	return get_group(group_id)['events'][event_id]

def process_events(group_id):
	_group = get_group(group_id)
	
	for event in _group['events'].values():
		events.process_event(event)

def announce(group_id, gist, message, consider_motive=False, **kwargs):
	_group = get_group(group_id)
	life = LIFE[_group['leader']]
	
	if consider_motive:
		if _group['claimed_motive'] == 'wealth':
			_announce_to = LIFE.keys()
			_announce_to.remove(life['id'])
		elif _group['claimed_motive'] == 'crime':
			_announce_to = judgement.get_trusted(life, visible=False)
		elif _group['claimed_motive'] == 'survival':
			_announce_to = LIFE.keys()
			_announce_to.remove(life['id'])
	else:
		_announce_to = _group['members']
		_announce_to.remove(life['id'])
	#TODO: Could have an option here to form an emergency "combat" group
	
	for life_id in _announce_to:
		speech.communicate(life,
	                      gist,
	                      msg=message,
	                      matches=[{'id': life_id}],
	                      **kwargs)

def get_shelter(group_id):
	return get_group(group_id)['shelter']

def find_shelter(life, group_id):
	_group = get_group(group_id)
	_group['shelter'] = judgement.get_best_shelter(life)
	
	if _group['shelter']:
		print 'SET SHELTER' * 100
		announce_shelter(group_id)

def announce_shelter(group_id):
	_group = get_group(group_id)
	distribute(LIFE[_group['leader']],
	           'group_set_shelter',
	           filter_by=get_event(group_id, _group['announce_event'])['accepted'],
	           chunk_id=_group['shelter'],
	           event_id=_group['announce_event'])

def find_and_announce_shelter(life, group_id):
	if get_shelter(group_id):
		announce_shelter(group_id)
	else:
		find_shelter(life, group_id)

def setup_group_events(group_id):
	_group = get_group(group_id)
	
	if stats.desires_shelter(LIFE[_group['leader']]) or 'player' in LIFE[_group['leader']]:
		_group['announce_event'] = add_event(group_id, events.create('shelter',
			action.make(return_function='find_and_announce_shelter'),
			{'life': action.make(life=_group['leader'], return_key='life'),
			 'group_id': group_id},
			fail_callback=action.make(return_function='desires_shelter'),
			fail_arguments={'life': action.make(life=_group['leader'], return_key='life')}))

def set_leader(group_id, life_id):
	_group = get_group(group_id)
	_group['leader'] = life_id
	
	set_motive(group_id, stats.get_group_motive(LIFE[life_id]))
	
	setup_group_events(group_id)
	
	lfe.memory(LIFE[life_id], 'became leader of group', group=group_id)
	logging.debug('%s is now the leader of group #%s' % (' '.join(LIFE[life_id]['name']), group_id))

def set_motive(group_id, motive):
	get_group(group_id)['claimed_motive'] = motive

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

def is_ready_to_shelter(group_id):
	_group = get_group(group_id)
	
	if get_total_trust(group_id)<0:
		return False
		
	if WORLD_INFO['ticks']-_group['last_updated'] >= len(_group['members'])*11:
		return True
	
	return False

def has_camp(group_id):
	for camp in WORLD_INFO['camps']:
		if camps.get_controlling_group_global(camp) == group_id:
			return camp
	
	return None

def get_jobs(group_id):
	_group = get_group(group_id)
	_jobs = []
	_leader = LIFE[_group['leader']]
	
	if not has_camp(group_id):
		_nearest_camp = camps.get_nearest_known_camp(_leader)
		
		if _leader['known_camps']:
			_j = jobs.create_job(_leader, 'Raid', gist='start_raid', description='Raid camp %s.' % _nearest_camp['id'])
			_pos = lfe.get_current_chunk(_leader)['pos']
		
			jobs.add_task(_j, '0', 'announce_to_group',
			              action.make_small_script(function='announce_to_group',
			                                       kwargs={'group_id': group_id,
			                                               'gist': 'job',
			                                               'message': jobs.get_job(_j)['description'],
			                                               'job_id': _j}),
			              description='Gather group members.')
			jobs.add_task(_j, '1', 'move_to_chunk',
			              action.make_small_script(function='travel_to_position',
			                                       kwargs={'pos': _pos}),
			              description='Travel to position %s, %s' % (_pos[0], _pos[1]),
				          delete_on_finish=False)
			jobs.add_task(_j, '2', 'wait_for_number_of_group_members_in_chunk',
			              action.make_small_script(function='number_of_alife_in_chunk_matching',
			                                       kwargs={'amount': 2,
			                                               'chunk_key': lfe.get_current_chunk_id(_leader),
			                                               'matching': {'group': _leader['group']}}),
			              description='Wait until everyone arrives.')
			#jobs.add_task(_j, '3', 'talk',
			#              action.make_small_script(function='travel_to_position',
			#                                       kwargs={'pos': chunks.get_nearest_chunk_in_list(_leader['pos'], camps.get_camp(_nearest_camp['id'])['reference'])}),
			#              requires=['1'],
			#              delete_on_finish=False)
			
			_jobs.append(_j)
	
	return _jobs

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

def is_leader_of_any_group(life):
	if not life['group']:
		return False
	
	return is_leader(life['group'], life['id'])
	
def delete_group(group_id):
	for member in get_group(group_id)['members']:
		remove_member(group_id, member)
		LIFE[member]['group'] = None
		logging.warning('Forcing removal of member \'%s\' from non-empty group #%s.' % (' '.join(LIFE[member]['name']), group_id)) 
	
	logging.warning('Deleted group: %s' % group_id)
	
	del WORLD_INFO['groups'][group_id]