from globals import *

import graphics as gfx
import life as lfe

import references
import judgement
import movement
import survival
import numbers
import memory
import action
import combat
import speech
import events
import chunks
import logic
import sight
import camps
import brain
import stats
import raids
import jobs

import logging
import random

def create_group(life, add_creator=True):
	WORLD_INFO['groupid'] += 1
	_id = str(WORLD_INFO['groupid']-1)
	
	discover_group(life, _id)
	
	if add_creator:
		join_group(life, _id)
		life['group'] = _id
	
	set_leader(life, _id, life['id'])
	
	return _id

def group_exists(life, group_id):
	return (group_id in life['known_groups'])

def get_group(life, group_id):
	if not group_exists(life, group_id):
		raise Exception('Group does not exist: %s' % group_id)
	
	return life['known_groups'][group_id]

def flag(life, group_id, flag, value):
	get_group(life, group_id)['flags'][flag] = value

def get_flag(life, group_id, flag):
	if not flag in get_group(life, group_id)['flags']:
		return None
	
	return get_group(life, group_id)['flags'][flag]

def discover_group(life, group_id):
	if not group_id in life['known_groups']:
		life['known_groups'][group_id] = {'id': group_id,
		                                  'members': [],
		                                  'leader': None,
		                                  'shelter': None,
		                                  'stage': STAGE_FORMING,
		                                  'alignment': 'neutral',
		                                  'claimed_motive': 'nothing',
		                                  'flags': {}}
		
		if 'player' in life:
			gfx.message('You learn about group %s.' % group_id)
		
		logging.debug('%s discovered group %s.' % (' '.join(life['name']), group_id))
		
		return True
	
	return False

def update_group_memory(life, group_id, flag, value):
	_previous_value = life['known_groups'][group_id][flag]
	life['known_groups'][group_id][flag] = value
	
	logging.debug('%s updated group %s\'s memory: %s: %s -> %s' % (' '.join(life['name']), group_id, flag, _previous_value, value))

def get_group_memory(life, group_id, flag):
	if not group_id in life['known_groups']:
		raise Exception('%s does not know about group %s.' % (' '.join(life['name']), group_id))
	
	return life['known_groups'][group_id][flag]

def get_group_relationships():
	_groups = {grp: {_grp: 0 for _grp in WORLD_INFO['groups'] if not _grp == grp} for grp in WORLD_INFO['groups']}

def join_group(life, group_id):
	life['group'] = group_id
	
	update_group_memory(life, group_id, 'alignment', 'trust')
	add_member(life, group_id, life['id'])
	
	if 'player' in life:
		gfx.message('You join group %s.' % group_id, style='good')
	else:
		logging.debug('%s joined group %s.' % (' '.join(life['name']), group_id))

def add_member(life, group_id, life_id):
	if not group_id in LIFE[life_id]['known_groups']:
		raise Exception('DOES NOT KNOW')
	
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
	
	for event in _group['events'].values():
		events.process_event(event)

def get_alignment(life, group_id):
	return get_group_memory(life, group_id, 'alignment')

def announce(life, _group_id, gist, message='', order=False, consider_motive=False, filter_if=[], **kwargs):
	_group = get_group(life, _group_id)
	
	if consider_motive:
		if _group['claimed_motive'] == 'wealth':
			_announce_to = []
			
			for life_id in LIFE.keys():
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
			
			for life_id in LIFE.keys():
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
		if filter_if and filter_if(LIFE[life_id]):
			continue
		
		#_sent = speech.has_sent(life, life_id, gist)
		#if _sent and WORLD_INFO['ticks']-_sent<15:
		#	continue
		
		if order:
			memory.create_order(life, life_id, gist, message, **kwargs)
		else:
			memory.create_question(life, life_id, gist, **kwargs)

def get_shelter(life, group_id):
	return get_group_memory(life, group_id, 'shelter')

def set_shelter(life, group_id, shelter):
	update_group_memory(life, group_id, 'shelter', shelter)

def find_shelter(life, group_id):
	_group = get_group(life, group_id)
	_shelter = judgement.get_best_shelter(life)
	
	if _shelter:
		set_shelter(life, group_id, chunks.get_chunk(_shelter)['reference'])
		announce(life, group_id, 'found_shelter')
	else:
		if get_stage(life, group_id) in [STAGE_FORMING]:
			set_stage(life, group_id, STAGE_SETTLING)
			announce(life, group_id, 'update_group_stage')

def find_and_announce_shelter(life, group_id):
	if get_stage(life, group_id) >= STAGE_RAIDING:
		return False
	
	_shelter = get_shelter(life, group_id)
	
	if get_motive(life, group_id) == 'crime' and logic.is_night():
		if _shelter:
			set_shelter(life, group_id, None)
			announce(life, group_id, 'update_group_shelter',
				    filter_if=lambda alife: not get_shelter(alife, group_id))
			
		#print 'MOTIVATED BY CRIME' * 20
		
		return False
	
	if _shelter:
		if get_stage(life, group_id) < STAGE_SETTLED:
			set_stage(life, group_id, STAGE_SETTLED)
		
		if references.is_in_reference(life['pos'], references.get_reference(_shelter)):
			announce(life, group_id, 'update_group_shelter',
				    filter_if=lambda alife: get_shelter(alife, group_id)==_shelter)
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
	update_group_memory(life, group_id, 'claimed_motive', motive)

def get_motive(life, group_id):
	return get_group_memory(life, group_id, 'claimed_motive')

def get_stage(life, group_id):
	return get_group_memory(life, group_id, 'stage')

def set_stage(life, group_id, stage):
	update_group_memory(life, group_id, 'stage', stage)

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
			
		
		print 'RAID', _lowest
	else:
		print 'ony one'
	
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
		
		if numbers.distance(life['pos'], chunks.get_chunk(chunk_key)['pos'])>50:
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
	_shelter = get_shelter(life, group_id)
	
	if not _shelter:
		return False
	
	_shelter_chunk = chunks.get_nearest_chunk_in_list(life['pos'], references.get_reference(_shelter))
	
	for known_group_id in life['known_groups']:
		if group_id == known_group_id:
			continue
		
		_opposing_shelter = get_possible_group_location(life, known_group_id)
		if not _opposing_shelter:
			continue
		
		_distance = chunks.get_distance_to_nearest_chunk_in_list(WORLD_INFO['chunk_map'][_shelter_chunk]['pos'], references.get_reference(_opposing_shelter))
		
		if _distance<=30:
			print '2 CLOSE 2 HANDLE'
	
	for seen_life_id in life['seen']:
		_target = brain.knows_alife_by_id(life, seen_life_id)
		
		if not _target or _target['alignment'] == 'trust' or not _target['last_seen_at'] or _target['dead']:
			continue
		
		if chunks.get_distance_to_nearest_chunk_in_list(_target['last_seen_at'], references.get_reference(_shelter))>30:
			continue
		
		memory.create_question(life, seen_life_id, 'territory_violation', ignore_if_said_in_last=-1)

def manage_raid(life, group_id):
	if not get_stage(life, group_id) in [STAGE_RAIDING, STAGE_ATTACKING]:
		return False
	
	_raid_chunk_key = get_flag(life, group_id, 'raid_chunk')
	
	if get_flag(life, group_id, 'announced_raid_location') == _raid_chunk_key:
		return False
	
	announce(life, group_id, 'raid_location', chunk_key=_raid_chunk_key)
	flag(life, group_id, 'announced_raid_location', _raid_chunk_key)
	lfe.memory(life, 'focus_on_chunk', chunk_key=_raid_chunk_key)
	
	print 'RAID LOCATION SET' * 100

def manage_combat(life, group_id):
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

	_confident = stats.is_confident(life)
	_enemy_focal_pos = None

	for target_id in _existing_targets:
		if not _enemy_focal_pos:
			_enemy_focal_pos = _existing_targets[target_id]['pos'][:]
		else:
			_enemy_focal_pos = numbers.lerp_velocity(_enemy_focal_pos, _existing_targets[target_id]['pos'], 0.5)
		
		if target_id in _checked_targets:
			continue
		
		_existing_targets[target_id]['time'] += 1
		
		if _existing_targets[target_id]['time']>100:
			del _existing_targets[target_id]
			
			continue
	
	_hostile_chunks = get_flag(life, group_id, 'hostile_chunks')
	_visible_chunks = get_flag(life, group_id, 'visible_chunks')
	
	if _enemy_focal_pos:
		if not _last_focal_point or numbers.distance(_enemy_focal_pos, _last_focal_point)>30:
			_hostile_chunks = chunks.get_visible_chunks_from((int(round(_enemy_focal_pos[0])), int(round(_enemy_focal_pos[1])), 2), life['vision_max']*1.5)
			_visible_chunks = chunks.get_visible_chunks_from(life['pos'], life['vision_max']*1.5)
			
			flag(life, group_id, 'hostile_chunks', _hostile_chunks)
			flag(life, group_id, 'visible_chunks', _visible_chunks)
			flag(life, group_id, 'last_focal_point', _enemy_focal_pos)
		#elif not _last_focal_point:
		#	flag(life, group_id, 'last_focal_point', _enemy_focal_pos)
			
	else:
		if get_stage(life, group_id) == STAGE_ATTACKING:
			set_stage(life, group_id, STAGE_FORMING)
		
		flag(life, group_id, 'friendlies', None)
		
		return False
	
	print life['name']
	print '%s ***** IN COMBAT *****' % group_id
	print '%s Enemy located near: %s' % (group_id, _enemy_focal_pos)
	print '%s ***** IN COMBAT *****' % group_id
	
	if not get_stage(life, group_id) == STAGE_ATTACKING:
		speech.announce_combat_to_group(life, group_id)
		set_stage(life, group_id, STAGE_ATTACKING)
	
	if not lfe.ticker(life, 'group_command_rate', 3):
		print 'Thinking'
		return False
	
	_orig_visible_chunks = _visible_chunks[:]
	
	#TODO: Check distance to threat
	for hostile_chunk_key in _hostile_chunks:
		if hostile_chunk_key in _visible_chunks:
			_visible_chunks.remove(hostile_chunk_key)
		
	#TODO: Additional stages: PLANNING, EXECUTING
	if _visible_chunks and stats.is_confident(life):
		for target_id in order_spread_out(life, group_id, _visible_chunks, filter_by=lambda target_id: WORLD_INFO['ticks']-_existing_friendlies[target_id]['updated']>100):
			_existing_friendlies[target_id]['updated'] = WORLD_INFO['ticks']
	else:
		_distant_chunk = {'distance': -1, 'chunk_key': None}
		
		for chunk_key in _orig_visible_chunks:
			_distance = numbers.distance((int(round(_enemy_focal_pos[0])), int(round(_enemy_focal_pos[1]))), chunks.get_chunk(chunk_key)['pos'])
			_distance *= numbers.clip(numbers.distance(life['pos'], _enemy_focal_pos), 1, 35)/35.0
			
			if chunk_key in _visible_chunks:
				_distance *= 2
			
			if _distance>_distant_chunk['distance']:
				_distant_chunk['distance'] = _distance
				_distant_chunk['chunk_key'] = chunk_key
		
		if _distant_chunk['chunk_key']:
			for target_id in order_move_to(life, group_id, _distant_chunk['chunk_key'], filter_by=lambda target_id: WORLD_INFO['ticks']-_existing_friendlies[target_id]['updated']>100):
				_existing_friendlies[target_id]['updated'] = WORLD_INFO['ticks']
		
		return False

#Might still work? Unsure... old code here
def manage_combat_old(life, group_id):
	if get_stage(life, group_id) == STAGE_RAIDING:
		prepare_for_raid(life, group_id)
		return False
	
	for known_group_id in life['known_groups']:
		if group_id == known_group_id:
			continue
		
		if get_group_memory(life, known_group_id, 'alignment') == 'neutral':
			_known_group_members = get_group_memory(life, known_group_id, 'members')
			
			announce(life, group_id, 'inform_of_known_group', group_id=known_group_id,
			         filter_if=lambda alife: group_exists(alife, known_group_id))
			
			if _known_group_members:
				update_group_memory(life, known_group_id, 'shelter', get_possible_group_location(life, known_group_id))
				
				_people_to_ask_about = []
				for member in _known_group_members:
					_target = brain.knows_alife_by_id(life, member)
					
					if not _target['last_seen_at'] or not _target['state'] in ['idle', 'shelter']:
						continue
					
					_people_to_ask_about.append(member)
				
				if get_group_memory(life, known_group_id, 'shelter'):
					fight_or_flight(life, group_id, known_group_id)
				elif _people_to_ask_about:
					announce(life, group_id, 'last_seen_target', target_id=random.choice(_people_to_ask_about))
				else:
					print 'Nobody to ask about group location'
					print 'LOST' * 100
		
		elif get_group_memory(life, known_group_id, 'alignment') == 'scared':
			_known_group_shelter = get_group(life, known_group_id)['shelter']
			
			if not _known_group_shelter:
				print 'FREE-FLOATING ANXIETY'
				continue
			
			_distance = chunks.get_distance_to_nearest_chunk_in_list(life['pos'], references.get_reference(_known_group_shelter))
			
			if get_stage(life, group_id) >= STAGE_SETTLED:
				if _distance<=100:
					set_stage(life, group_id, STAGE_SETTLING)
					set_shelter(life, group_id, None)
			#if get_stage(life, group_id) == STAGE_SETTLED:
			#	set_stage(life, group_id, STAGE_RAIDING)
			#	
			#	announce(life, group_id, 'prepare_for_raid')
			#	flag(life, group_id, 'raid_target', known_group_id)
			
			#declare_group_hostile(life, group_id, known_group_id)

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
		print 'STILL DO NOT HAVE TARGET GROUP LOCATION'
	
	return _most_recent['shelter']

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
	         filter_if=lambda alife: brain.get_alife_flag(life, alife['id'], 'combat_ready'))

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
		
		if life['id'] == life_id:
			movement.guard_chunk(life, random.choice(chunk_keys))
			
			continue
		
		_ordered_targets.append(life_id)
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