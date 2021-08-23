from globals import *

import graphics as gfx
import life as lfe

from . import references
from . import judgement
from . import movement
from . import survival
from . import factions
import bad_numbers
from . import memory
from . import action
from . import combat
from . import speech
import events
from . import chunks
import logic
from . import sight
from . import camps
from . import brain
from . import stats
from . import raids
from . import jobs

import logging
import random


def create_group(life, add_creator=True):
	WORLD_INFO['groupid'] += 1
	_id = str(WORLD_INFO['groupid']-1)
	
	WORLD_INFO['groups'][_id] = {'id': _id,
	                             'members': [],
	                             'leader': None,
	                             'shelter': None,
	                             'stage': STAGE_FORMING,
	                             'alignment': 'neutral',
	                             'claimed_motive': 'nothing',
	                             'flags': {}}
	
	if add_creator:
		join_group(life, _id)
		life['group'] = _id
	
	set_leader(life, _id, life['id'])
	
	return _id

def group_exists(life, group_id):
	return (group_id in WORLD_INFO['groups'])

def get_group(life, group_id):
	#if not group_exists(life, group_id):
	#	raise Exception('Group does not exist: %s' % group_id)
	
	return WORLD_INFO['groups'][group_id]

def flag(life, group_id, flag, value):
	get_group(life, group_id)['flags'][flag] = value

def get_flag(life, group_id, flag):
	if not flag in get_group(life, group_id)['flags']:
		return None
	
	return get_group(life, group_id)['flags'][flag]

def has_flag(life, group_id, flag):
	return flag in get_group(life, group_id)['flags']

def get_group_size(life, group_id):
	_number_of_members = len(get_group(life, group_id)['members'])
	
	if _number_of_members>=5:
		return 'large'
	
	if _number_of_members>2:
		return 'small'
	
	return 'partner'

def get_group_relationships():
	_groups = {grp: {_grp: 0 for _grp in WORLD_INFO['groups'] if not _grp == grp} for grp in WORLD_INFO['groups']}

def join_group(life, group_id):
	life['group'] = group_id
	
	add_member(life, group_id, life['id'])
	
	if 'player' in life:
		gfx.message('You join group %s.' % group_id, style='good')
	else:
		logging.debug('%s joined group %s.' % (' '.join(life['name']), group_id))

def add_member(life, group_id, life_id):
	if is_member(life, group_id, life_id):
		raise Exception('%s failed to add new member: %s is already a member of group: %s' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name']), group_id))
	
	if not life['id'] == life_id:
		_target = brain.knows_alife_by_id(life, life_id)
		
		if _target:
			if _target['group'] == group_id:
				pass
			elif _target and _target['group']:
				lfe.memory(LIFE[life_id], 'left group for group', left_group=_target['group'], group=group_id)
				remove_member(life, _target['group'], life_id)
			
			_target['group'] = group_id
		else:
			_target = brain.meet_alife(life, LIFE[life_id])
		
		stats.establish_trust(life, life_id)
	elif life['id'] == life_id and life['group'] and not life['group'] == group_id:
		remove_member(life, life['group'], life_id)
	
	_group = get_group(life, group_id)
	for member in _group['members']:
		brain.meet_alife(LIFE[member], LIFE[life_id])
	
	if _group['shelter']:
		LIFE[life_id]['shelter'] = _group['shelter']
		lfe.memory(LIFE[life_id], 'shelter founder', shelter=_group['shelter'], founder=_group['leader'])
	
	_group['members'].append(life_id)
	
	if _group['leader'] and 'player' in LIFE[_group['leader']]:
		_text = '%s has joined your group.' % ' '.join(LIFE[life_id]['name'])
		gfx.message(_text, style='good')
		
		if sight.can_see_target(LIFE[_group['leader']], life_id):
			logic.show_event(_text, life=LIFE[life_id], delay=1)
	
	logging.debug('%s added %s to group \'%s\'' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name']), group_id))

def remove_member(life, group_id, life_id):
	_group = get_group(life, group_id)
	
	if not is_member(life, group_id, life_id):
		raise Exception('%s is not a member of group: %s' % (' '.join(LIFE[life_id]['name']), group_id))
	
	_group['members'].remove(life_id)
	
	#reconfigure_group(life, group_id)

def reconfigure_group(life, group_id):
	_group = get_group(life, group_id)
	
	if not is_member(life, group_id, _group['leader']):
		logging.debug('Leader \'%s\' is leaving group #%s' % (' '.join(LIFE[_group['leader']]['name']), group_id))
	
	_successor = find_successor(life, group_id, assign=True)
	
	if _successor:
		logging.debug('\'%s\' is now leader of group #%s' % (' '.join(LIFE[_successor]['name']), group_id))
	else:
		logging.error('No successor could be found for group #%s (THIS SHOULD NOT HAPPEN)' % group_id)

def find_successor(life, group_id, assign=False):
	_group = get_group(life, group_id)
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

def distribute(life, message, filter_by=[], **kvargs):
	_group = get_group(life, life['group'])
	
	for member in _group['members']:
		if member in filter_by:
			continue
		
		speech.communicate(life, message, radio=True, matches=[member], **kvargs)

def add_job(life, group_id, job_id):
	_group = get_group(life, group_id)
	
	#TODO: Remove
	if not 'jobs' in _group:
		_group['jobs'] = []
	
	_group['jobs'].append(job_id)
	
	logging.debug('Registered job %s with group %s' % (job_id, group_id))

def add_event(life, group_id, event):
	_group = get_group(life, group_id)
	
	_group['events'][str(_group['event_id'])] = event
	_group['event_id'] += 1
	
	return str(_group['event_id']-1)

def get_event(life, group_id, event_id):
	return get_group(life, group_id)['events'][event_id]

def process_events(life, group_id):
	_group = get_group(life, group_id)
	
	for event in list(_group['events'].values()):
		events.process_event(event)

def announce(life, _group_id, gist, message='', order=False, consider_motive=False, filter_if=None, **kwargs):
	_group = get_group(life, _group_id)
	
	if consider_motive:
		if _group['claimed_motive'] == 'wealth':
			_announce_to = []
			
			for life_id in list(LIFE.keys()):
				if life_id == life['id']:
					continue
				
				if stats.is_same_species(life, life_id):
					_announce_to.append(life_id)
		elif _group['claimed_motive'] in ['crime', 'military']:
			_announce_to = judgement.get_trusted(life, visible=False)

			for life_id in _announce_to[:]:
				if not stats.is_same_species(life, life_id):
					_announce_to.remove(life_id)
			
		elif _group['claimed_motive'] == 'survival':
			_announce_to = []
			
			for life_id in list(LIFE.keys()):
				if life_id == life['id']:
					continue
				
				if stats.is_same_species(life, life_id):
					_announce_to.append(life_id)
			
	else:
		_announce_to = _group['members'][:]
		
		if life['id'] in _announce_to:
			_announce_to.remove(life['id'])
	#TODO: Could have an option here to form an emergency "combat" group
	
	for life_id in _announce_to:
		if filter_if and filter_if(life_id):
			continue
		
		#_sent = speech.has_sent(life, life_id, gist)
		#if _sent and WORLD_INFO['ticks']-_sent<15:
		#	continue
		
		if order:
			memory.create_order(life, life_id, gist, message, **kwargs)
		else:
			memory.create_question(life, life_id, gist, **kwargs)

def get_shelter(life, group_id):
	_group = get_group(life, group_id)
	
	return _group['shelter']

def set_shelter(life, group_id, shelter):
	_group = get_group(life, group_id)
	_group['shelter'] = shelter

def find_shelter(life, group_id):
	_group = get_group(life, group_id)
	_shelter = judgement.get_best_shelter(life)
	
	if _shelter:
		set_shelter(life, group_id, chunks.get_chunk(_shelter)['reference'])
		announce(life, group_id, 'found_shelter')
	else:
		if get_stage(life, group_id) in [STAGE_FORMING]:
			set_stage(life, group_id, STAGE_SETTLING)

def find_and_announce_shelter(life, group_id):
	if get_stage(life, group_id) >= STAGE_RAIDING:
		return False
	
	_shelter = get_shelter(life, group_id)
	
	if get_motive(life, group_id) == 'crime' and logic.is_night():
		if _shelter:
			set_shelter(life, group_id, None)
			announce(life, group_id, 'update_group_shelter',
				    filter_if=lambda alife_id: not get_shelter(LIFE[alife_id], group_id))
			
		#print 'MOTIVATED BY CRIME' * 20
		
		return False
	
	if _shelter:
		if get_stage(life, group_id) < STAGE_SETTLED:
			set_stage(life, group_id, STAGE_SETTLED)
		
		if references.is_in_reference(life['pos'], references.get_reference(_shelter)):
			announce(life, group_id, 'update_group_shelter',
				    filter_if=lambda alife_id: get_shelter(LIFE[alife_id], group_id)==_shelter)
	else:
		find_shelter(life, group_id)

def get_leader(life, group_id):
	return get_group(life, group_id)['leader']

def set_leader(life, group_id, life_id):
	_group = get_group(life, group_id)
	_group['leader'] = life_id
	
	set_motive(life, group_id, stats.get_group_motive(LIFE[life_id]))
	
	lfe.memory(LIFE[life_id], 'claimed to be the leader of group', group=group_id)
	logging.debug('%s claims to be the leader of group #%s' % (' '.join(LIFE[life_id]['name']), group_id))

def raid(life, group_id, chunk_key):
	flag(life, group_id, 'raid_chunk', chunk_key)

def set_motive(life, group_id, motive):
	_group = get_group(life, group_id)
	_group['claimed_motive'] = motive

def get_motive(life, group_id):
	_group = get_group(life, group_id)
	
	return _group['claimed_motive']

def get_stage(life, group_id):
	_group = get_group(life, group_id)
	
	return _group['stage']

def set_stage(life, group_id, stage):
	_group = get_group(life, group_id)
	_group['stage'] = stage

def get_combat_score(life, group_id, potential=False):
	_group = get_group(life, group_id)
	_score = 0
	
	for member in [LIFE[l] for l in _group['members']]:
		if combat.get_best_weapon(member):
			if not potential and not combat.weapon_equipped_and_ready(member):
				continue
			
			_score += 1
	
	return _score

def get_potential_combat_score(life, group_id):
	return get_combat_score(life, group_id, potential=True)

def get_status(life, group_id):
	_group = get_group(life, group_id)
	
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

def get_unwanted_members_with_perspective(life, group_id):
	_group = get_group(life, group_id)
	_untrusted = []
	
	for member in [m for m in _group['members'] if not life['id'] == m]:
		if judgement.can_trust(life, member):
			continue
		
		_untrusted.append(member)
	
	return _untrusted

def has_camp(group_id):
	for camp in WORLD_INFO['camps']:
		if camps.get_controlling_group_global(camp) == group_id:
			return camp
	
	return None

def get_jobs(life, group_id):
	_group = get_group(life, group_id)
	_jobs = []
	_leader = LIFE[_group['leader']]
	
	if not has_camp(group_id):
		_nearest_camp = camps.get_nearest_known_camp(_leader)
		
		if _leader['known_camps']:
			_j = jobs.create_job(_leader, 'Raid', gist='start_raid', description='Raid camp %s.' % _nearest_camp['id'])
			_pos = lfe.get_current_chunk(_leader)['pos']
			_chunk_key = lfe.get_current_chunk_id(_leader)
		
			jobs.add_task(_j, '0', 'announce_to_group',
			              action.make_small_script(function='announce_to_group',
			                                       kwargs={'group_id': group_id,
			                                               'gist': 'announce_group_job',
			                                               'message': jobs.get_job(_j)['description'],
			                                               'job_id': _j}),
			              player_action=action.make_small_script(function='always'),
			              description='Gather group members.')
			jobs.add_task(_j, '1', 'move_to_chunk',
			              action.make_small_script(function='travel_to_position',
			                                       kwargs={'pos': _pos}),
			              player_action=action.make_small_script(function='is_in_chunk',
	                                           kwargs={'chunk_key': _chunk_key}),
			              description='Travel to position %s, %s' % (_pos[0], _pos[1]),
				          delete_on_finish=False)
			jobs.add_task(_j, '2', 'wait_for_number_of_group_members_in_chunk',
			              action.make_small_script(function='number_of_alife_in_chunk_matching',
			                                       kwargs={'amount': 2,
			                                               'chunk_key': _chunk_key,
			                                               'matching': {'group': _leader['group']}}),
			              description='Wait until everyone arrives.')
			#jobs.add_task(_j, '3', 'talk',
			#              action.make_small_script(function='travel_to_position',
			#                                       kwargs={'pos': chunks.get_nearest_chunk_in_list(_leader['pos'], camps.get_camp(_nearest_camp['id'])['reference'])}),
			#              requires=['1'],
			#              delete_on_finish=False)
			
			_jobs.append(_j)
	
	if len(_leader['known_groups'])>1:
		_lowest = {'score': 0, 'group': None}
		for group_id in [g for g in _leader['known_groups'] if not g==_leader['group']]:
			_score = judgement.judge_group(_leader, group_id)
			
			if not _lowest['group'] or _score < _lowest['score']:
				_lowest['score'] = _score
				_lowest['group'] = group_id
			
		
		print('RAID', _lowest)
	else:
		print('ony one')
	
	return _jobs

def manage_resources(life, group_id):
	_group = get_group(life, group_id)
	_last_resource_check = get_flag(life, group_id, 'last_resource_count')
	
	if _last_resource_check and WORLD_INFO['ticks']-_last_resource_check<=100:
		return True
	
	announce(life, group_id, 'resource_check', ignore_if_said_in_last=3000)
	
	flag(life, group_id, 'last_resource_count', WORLD_INFO['ticks'])

def manage_known_groups(life, group_id):
	for known_group_id in life['known_groups']:
		if group_id == known_group_id:
			continue
		
		_known_members = life['known_groups'][known_group_id]['members']
		if not _known_members:
			speech.announce(life, 'ask_for_group_list', trusted=True, group_id=known_group_id, ignore_if_said_in_last=3000)
		elif len(_known_members)<=3:
			speech.announce(life, 'ask_for_group_list', group=known_group_id, group_id=known_group_id, ignore_if_said_in_last=3000)

def manage_jobs(life, group_id):
	_shelter = get_shelter(life, group_id)
	
	if not _shelter:
		return False
	
	if not get_stage(life, group_id) == STAGE_SETTLED:
		return False
	
	if get_flag(life, life['group'], 'guard_chunk_keys'):
		return False
	
	_guard_chunk_keys = []
	_potential_guard_chunk_keys = []
	_group_members = get_group(life, life['group'])['members']
	_shelter_chunks = references.get_reference(_shelter)[:]
	
	#TODO: This is horrible... like the worst possible way to do this
	for chunk_key in WORLD_INFO['chunk_map']:
		if chunk_key in _shelter_chunks:
			_shelter_chunks.remove(chunk_key)
			continue
		
		if bad_numbers.distance(life['pos'], chunks.get_chunk(chunk_key)['pos'])>50:
			continue
		
		_potential_guard_chunk_keys.append(chunk_key)
	
	if not _potential_guard_chunk_keys:
		return False
	
	for member_id in _group_members:
		if member_id == life['id']:
			continue
		
		_chunk_key = _potential_guard_chunk_keys.pop(random.randint(0, len(_potential_guard_chunk_keys)-1))
		_guard_chunk_keys.append(_chunk_key)
		lfe.memory(LIFE[member_id], 'focus_on_chunk', chunk_key=_chunk_key)
		
		if not _potential_guard_chunk_keys:
			break
	
	flag(life, life['group'], 'guard_chunk_keys', _guard_chunk_keys)

def manage_territory(life, group_id):
	if get_stage(life, group_id) == STAGE_ATTACKING:
		return False
	
	_shelter = get_shelter(life, group_id)
	
	if not _shelter:
		return False
	
	_shelter_chunk = chunks.get_nearest_chunk_in_list(life['pos'], factions.get_territory(_shelter)['chunk_keys'])
	
	for known_group_id in life['known_groups']:
		if group_id == known_group_id:
			continue
		
		_opposing_shelter = get_possible_group_location(life, known_group_id)
		if not _opposing_shelter:
			continue
		
		_distance = chunks.get_distance_to_nearest_chunk_in_list(WORLD_INFO['chunk_map'][_shelter_chunk]['pos'], factions.get_territory(_opposing_shelter)['chunk_keys'])
		
		if _distance<=30:
			print('2 CLOSE 2 HANDLE')

def manage_raid(life, group_id):
	if not get_stage(life, group_id) in [STAGE_RAIDING, STAGE_ATTACKING]:
		return False
	
	_raid_chunk_key = get_flag(life, group_id, 'raid_chunk')
	
	if get_flag(life, group_id, 'announced_raid_location') == _raid_chunk_key:
		return False
	
	announce(life, group_id, 'raid_location', chunk_key=_raid_chunk_key)
	flag(life, group_id, 'announced_raid_location', _raid_chunk_key)
	lfe.memory(life, 'focus_on_chunk', chunk_key=_raid_chunk_key)
	
	print('RAID LOCATION SET' * 100)

def manage_combat(life, group_id):
	if has_flag(life, group_id, 'confident'):
		_was_confident = get_flag(life, group_id, 'confident')
		
		if _was_confident == stats.is_confident(life) and not lfe.ticker(life, 'decision_wait', 16):
			return False
	
	flag(life, group_id, 'confident', stats.is_confident(life))
	
	_existing_friendlies = get_flag(life, group_id, 'friendlies')
	_existing_targets = get_flag(life, group_id, 'targets')
	_last_focal_point = get_flag(life, group_id, 'last_focal_point')
	
	if not _existing_friendlies:
		_existing_friendlies = {}
	
	if not _existing_targets:
		_existing_targets = {}
	
	for life_id in get_group(life, group_id)['members']:
		if not life_id in _existing_friendlies:
			_existing_friendlies[life_id] = {'updated': -900}
	
	flag(life, group_id, 'friendlies', _existing_friendlies)
	
	_checked_targets = []
	for target_id in judgement.get_threats(life):
		if target_id in _existing_targets:
			_existing_targets[target_id]['time'] = 0
		else:
			_existing_targets[target_id] = {'time': 0, 'pos': brain.knows_alife_by_id(life, target_id)['last_seen_at'][:]}
		
		_checked_targets.append(target_id)

	_enemy_focal_pos = None

	for target_id in _existing_targets:
		if not _enemy_focal_pos:
			_enemy_focal_pos = _existing_targets[target_id]['pos'][:]
		else:
			_enemy_focal_pos = bad_numbers.lerp_velocity(_enemy_focal_pos, _existing_targets[target_id]['pos'], 0.5)
		
		if target_id in _checked_targets:
			continue
		
		_existing_targets[target_id]['time'] += 1
		
		if _existing_targets[target_id]['time']>100:
			del _existing_targets[target_id]
			
			continue
	
	_hostile_chunks = get_flag(life, group_id, 'hostile_chunks')
	_previous_visible_chunks = brain.get_flag(life, 'group_combat_vis_chunks')
	
	if _previous_visible_chunks and _previous_visible_chunks['from_pos'] == life['pos']:
		_visible_chunks = _previous_visible_chunks['visible_chunks']
	else:
		_visible_chunks = chunks.get_visible_chunks_from(life['pos'], life['vision_max']*.75)
		
		brain.flag(life, 'group_combat_vis_chunks', value={'from_pos': life['pos'][:],
		                                                   'visible_chunks': _visible_chunks})
	
	if _enemy_focal_pos:
		lfe.clear_ticker(life, 'group_command_reset')
		
		if not _last_focal_point or bad_numbers.distance(_enemy_focal_pos, _last_focal_point)>30:
			_hostile_chunks = chunks.get_visible_chunks_from((int(round(_enemy_focal_pos[0])), int(round(_enemy_focal_pos[1])), 2), life['vision_max']*1.5)
			
			flag(life, group_id, 'hostile_chunks', _hostile_chunks)
			flag(life, group_id, 'visible_chunks', _visible_chunks)
			flag(life, group_id, 'last_focal_point', _enemy_focal_pos)
			
	else:
		_ticker = lfe.ticker(life, 'group_command_reset', 48)
		
		if get_stage(life, group_id) == STAGE_ATTACKING:
			if _ticker:
				set_stage(life, group_id, STAGE_FORMING)
				flag(life, group_id, 'friendlies', None)
				flag(life, group_id, 'strategy', None)
			else:
				manage_strategy(life, group_id)
		
		return False
	
	if not get_stage(life, group_id) == STAGE_ATTACKING:
		speech.announce_combat_to_group(life, group_id)
		set_stage(life, group_id, STAGE_ATTACKING)
	
	if not lfe.ticker(life, 'group_command_rate', 3):
		return False
	
	_orig_visible_chunks = _visible_chunks[:]
	
	#TODO: Check distance to threat
	for hostile_chunk_key in _hostile_chunks:
		if hostile_chunk_key in _visible_chunks:
			_visible_chunks.remove(hostile_chunk_key)
		
	#TODO: Additional stages: PLANNING, EXECUTING
	if _visible_chunks and stats.is_confident(life):
		for target_id in order_spread_out(life, group_id, _visible_chunks, filter_by=lambda life_id: WORLD_INFO['ticks']-_existing_friendlies[life_id]['updated']>100):
			_existing_friendlies[target_id]['updated'] = WORLD_INFO['ticks']
	else:
		_distant_chunk = {'distance': -1, 'chunk_key': None}
		_unchecked_members = get_group(life, group_id)['members'][:]
		
		for chunk_key in _orig_visible_chunks:
			_distance = bad_numbers.distance((int(round(_enemy_focal_pos[0])), int(round(_enemy_focal_pos[1]))), chunks.get_chunk(chunk_key)['pos'])
			_distance *= bad_numbers.clip(bad_numbers.distance(life['pos'], _enemy_focal_pos), 1, 35)/35.0
			
			if chunk_key in _visible_chunks:
				_distance *= 2
			
			for member_id in _unchecked_members:
				if life['id'] == member_id:
					continue
				
				_target = brain.knows_alife_by_id(life, member_id)
				
				if _target['last_seen_time'] <= 25 and chunks.get_chunk_key_at(_target['last_seen_at']) == chunk_key:
					_distance *= (2.5*(1-(bad_numbers.clip(_target['last_seen_time'], 0, 25)/25.0)))
			
			if _distance>_distant_chunk['distance']:
				_distant_chunk['distance'] = _distance
				_distant_chunk['chunk_key'] = chunk_key
		
		if _distant_chunk['chunk_key']:
			for target_id in order_move_to(life, group_id, _distant_chunk['chunk_key'], filter_by=lambda life_id: WORLD_INFO['ticks']-_existing_friendlies[life_id]['updated']>100):
				_existing_friendlies[target_id]['updated'] = WORLD_INFO['ticks']
		
		return False

def manage_strategy(life, group_id):
	_last_strat = get_flag(life, group_id, 'strategy')
	
	if _last_strat and _last_strat['ready'] and WORLD_INFO['ticks']-_last_strat['updated']<100:
		return False
	
	if _last_strat:
		_strat = _last_strat
	else:
		_strat = {'ready': False, 'gear_track': {}}
		
	flag(life, group_id, 'strategy', _strat)
	
	_gear_track = _strat['gear_track']
	_group = get_group(life, group_id)
	_members_combat_ready = 0
	
	#Get inventory...
	for member_id in _group['members']:
		#TODO: Handle this
		if member_id == life['id']:
			continue
		
		if not member_id in _gear_track:
			_gear_track[member_id] = {'has_weapon': len(lfe.get_all_equipped_items(LIFE[member_id], matches=[{'type': 'gun'}]))>0,
			                          'has_ammo': False,
			                          'asked': [],
			                          'mia': False}
		
		_track = _gear_track[member_id]

		if brain.knows_alife_by_id(life, member_id)['last_seen_time'] <= 100:
			if 'mia_check' in _track['asked']:
				_track['asked'].remove('mia_check')
			
			_track['mia'] = False
		else:
			_track['mia'] = True
		
		if _track['mia']:
			if not 'mia_check' in _track['asked']:
				_track['asked'].append('mia_check')
				_size = get_group_size(life, group_id)
				
				memory.create_question(life, member_id, 'order_status_report_%s' % _size)
		elif _track['has_weapon']:
			if _track['has_ammo']:
				_members_combat_ready.append(member_id)
		elif not 'order_equip_weapon' in _track['asked']:
			_track['asked'].append('order_equip_weapon')
			
			memory.create_question(life, member_id, 'order_equip_weapon')

def get_possible_group_location(life, group_id):
	_group = get_group(life, group_id)
	_most_recent = {'time': 9999, 'shelter': None}
	
	for member in _group['members']:
		_target = brain.knows_alife_by_id(life, member)
		
		if not _target['last_seen_at'] or not _target['state'] in ['shelter', 'idle']:
			continue
		
		if _target['last_seen_time'] < _most_recent['time'] or not _most_recent['shelter']:
			_most_recent['shelter'] = references.is_in_any_reference(_target['last_seen_at'])
			_most_recent['time'] = _target['last_seen_time']
	
	if not _most_recent['shelter']:
		print('STILL DO NOT HAVE TARGET GROUP LOCATION')
	
	return _most_recent['shelter']

def is_group_hostile(life, group_id):
	return factions.is_enemy(life, get_group(life, group_id)['leader'])

def is_target_group_hostile(life, life_id):
	if not brain.knows_alife_by_id(life, life_id) or not brain.knows_alife_by_id(life, life_id)['group']:
		return False
	
	return factions.is_enemy(life, get_group(life, LIFE[life_id]['group'])['leader'])

def is_combat_ready(life, group_id):
	_combat_readiness = 0
	
	for member in get_group(life, group_id)['members']:
		if life['id'] == member:
			continue
		
		_combat_readiness += brain.get_alife_flag(life, member, 'combat_ready')
	
	if _combat_readiness >= 3:
		#update_group_memory(life, target_group_id, 'al
		return True
	else:
		return False

def fight_or_flight(life, group_id, target_group_id):
	_distance = chunks.get_distance_to_nearest_chunk_in_list(life['pos'], references.get_reference(get_shelter(life, target_group_id)))
	
	if is_combat_ready(life, group_id):
		stats.declare_group_hostile(life, target_group_id)
	elif _distance<=100:
		stats.declare_group_scared(life, target_group_id)
	else:
		prepare_for_raid(life, group_id)

def prepare_for_raid(life, group_id):
	#_target_group = get_flag(life, group_id, 'raid_target')
	
	announce(life, group_id, 'combat_ready', ignore_if_said_in_last=1000,
	         filter_if=lambda alife_id: brain.get_alife_flag(life, LIFE[alife_id], 'combat_ready'))

def declare_group_hostile(life, group_id, target_group_id):
	stats.declare_group_hostile(life, target_group_id)
	
	announce(life, group_id, 'group_is_hostile', group_id=target_group_id)

def is_member(life, group_id, life_id):
	_group = get_group(life, group_id)
	
	if life_id in _group['members']:
		return True
	
	return False

def order_to_loot(life, group_id, add_leader=False):
	#TODO: We should really consider moving the needs portion of this code outside of this function
	#Because this function really only does something on the first run, rendering it into just another
	#announce loop...
	
	_group = get_group(life, group_id)
	
	_requirements = [action.make_small_script(function='has_number_of_items_matching',
	                                          args={'matching': [{'type': 'drink'}], 'amount': 1})]
	
	_j = jobs.create_job(life, 'Loot for group %s.' % life['group'],
	                     gist='loot_for_group',
	                     description='Collect loot for group.',
	                     group=life['group'],
	                     requirements=_requirements)
	
	if _j:
		for member in _group['members']:
			if member == _group['leader'] and not add_leader:
				continue
			
			survival.add_needed_item(LIFE[member],
				                    {'type': 'drink'},
				                    amount=1,
			                         pass_if=_requirements,
				                    satisfy_if=action.make_small_script(function='group_needs_resources',
				                                                        args={'group_id': group_id}),
				                    satisfy_callback=action.make_small_script(return_function='pass'))
		
		jobs.add_task(_j, '0', 'bring_back_loot',
		              action.make_small_script(function='find_target',
		                                       kwargs={'target': _group['leader'],
		                                               'distance': 5,
		                                               'follow': False}),
		              player_action=action.make_small_script(function='can_see_target',
		                                                     kwargs={'target_id': _group['leader']}),
		              description='Drop the item off at the camp',
		              delete_on_finish=False)
		
		jobs.add_task(_j, '1', 'flag_item',
		              action.make_small_script(function='flag_item_matching',
		                                       kwargs={'matching': {'type': 'drink'},
		                                               'flag': 'ignore'}),
		              player_action=action.make_small_script(function='always'),
		              description='Ignore this',
		              delete_on_finish=False)
		
		jobs.add_task(_j, '2', 'drop_item',
		              action.make_small_script(function='drop_item_matching',
		                                       kwargs={'matching': {'type': 'drink'}}),
		              player_action=action.make_small_script(function='never'),
		              description='Drop the item off at the camp',
		              delete_on_finish=False)
		
		flag(group_id, 'loot', _j)
	
	if lfe.ticker(life, 'resource_announce', 10):
		_job_id = get_flag(group_id, 'loot')
		
		announce(life, life['group'],
			     'job',
			     'We need more resources.',
			     job_id=_job_id,
		          order=True,
			     filter_if=[action.make_small_script(function='has_needs_to_meet')])

def order_spread_out(life, group_id, chunk_keys, filter_by=None):
	_group = get_group(life, group_id)
	_ordered_targets = []
	
	for life_id in _group['members']:
		if not filter_by(life_id):
			continue
		
		if life_id == life['id']:
			movement.set_focus_point(life, random.choice(chunk_keys))
			
			continue
		
		_ordered_targets.append(life_id)
		
		if lfe.get_current_chunk_id(LIFE[life_id]) in chunk_keys:
			speech.start_dialog(life, life_id, 'order_wait_%s' % get_group_size(life, group_id), remote=True)
		else:
			speech.start_dialog(life, life_id, 'order_move_to_chunk', chunk_key=random.choice(chunk_keys), remote=True)
	
	return _ordered_targets

def order_move_to(life, group_id, chunk_key, filter_by=None):
	return order_spread_out(life, group_id, [chunk_key], filter_by=filter_by)

def is_leader(life, group_id, life_id):
	_group = get_group(life, group_id)
	
	if life_id == _group['leader']:
		return True
	
	return False

def is_leader_of_any_group(life):
	if not life['group']:
		return False
	
	return is_leader(life, life['group'], life['id'])