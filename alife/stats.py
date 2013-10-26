from globals import *

import life as lfe

import historygen
import judgement
import survival
import groups
import combat
import camps
import sight
import brain
import zones

import numbers
import logging
import random

MAX_INFLUENCE_FROM = 80
MAX_INTROVERSION = 10
MAX_CHARISMA = 9

def init(life):
	life['stats'] = historygen.create_background(life)
	#life['stats']['charisma'] = random.randint(1, MAX_CHARISMA)

def desires_job(life):
	#TODO: We recalculate this, but the answer is always the same.
	
	_wont = brain.get_flag(life, 'wont_work')
	if life['job'] or _wont:
		if _wont:
			_wont = brain.flag(life, 'wont_work', value=_wont-1)
			
		return False
	
	if not life['stats']['lone_wolf']:
		return True
	
	brain.flag(life, 'wont_work', value=1000)
	return False

def desires_life(life, life_id):
	if not lfe.execute_raw(life, 'judge', 'factors', life_id=life_id):
		return False
	
	return True

def desires_interaction(life):
	if not lfe.execute_raw(life, 'talk', 'desires_interaction'):
		return False
	
	return True

def desires_conversation_with(life, life_id):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	if not _knows:
		logging.error('FIXME: Improperly Used Function: Doesn\'t know talking target.')
		return False
	
	if not lfe.execute_raw(life, 'talk', 'desires_conversation_with', life_id=life_id):
		return False
	
	if not judgement.can_trust(life, life_id):
		return False
	
	return True

def desires_to_create_group(life):
	if life['group']:
		return False
	
	if not lfe.execute_raw(life, 'group', 'create_group'):
		return False
	
	return True

def wants_to_abandon_group(life, group_id, with_new_group_in_mind=None):
	if with_new_group_in_mind:
		if judgement.judge_group(life, with_new_group_in_mind)>get_minimum_group_score(life):
			return True
	
	_group = groups.get_group(group_id)
	if WORLD_INFO['ticks']-_group['time_created']<life['stats']['patience']:
		return False
	
	_top_group = {'id': -1, 'score': 0}
	for memory in lfe.get_memory(life, matches={'group': '*'}):
		if not memory['group'] in WORLD_INFO['groups']:
			continue
		
		_score = 0
		
		if 'trust' in memory:
			_score += memory['trust']
		
		if 'danger' in memory:
			_score += memory['danger']
	
		if _score > _top_group['score'] or _top_group['id'] == -1:
			_top_group['id'] = memory['group']
			_top_group['score'] = _score
		
	if _top_group['score']:
		if judgement.judge_group(life, _top_group['id'])>get_minimum_group_score(life):
			return True
	
	return False

def desires_group(life, group_id):
	if life['group']:
		return wants_to_abandon_group(life, life['group'], with_new_group_in_mind=group_id)
	
	if judgement.judge_group(life, group_id)>get_minimum_group_score(life):
		return True
	
	return False

def desires_to_create_camp(life):
	if not 'CAN_GROUP' in life['life_flags']:
		return False
		
	if life['group'] and not groups.get_camp(life['group']) and groups.is_leader(life['group'], life['id']):
		if len(groups.get_group(life['group'])['members'])>1:
			return True
	
	return False

def desires_shelter(life):
	if not lfe.execute_raw(life, 'discover', 'desires_shelter'):
		return False
	
	#TODO: Why?
	if life['state'] == 'needs':
		return False
	
	return True

def desires_to_join_camp(life, camp_id):
	if life['group']:
		return False
	
	if life['camp']:
		print life['name'],'already has camp',camps.knows_founder(life, life['camp'])
		return False
	
	if life['stats']['lone_wolf']:
		return False
	
	_memories = lfe.get_memory(life, matches={'text': 'heard_about_camp', 'camp': camp_id, 'founder': '*'})
	if _memories:
		_memory = _memories.pop()
		
		if not judgement.can_trust(life, _memory['founder']):
			print life['name'],'Cant trust founder' * 10
			return False
		
	if lfe.get_memory(life, matches={'text': 'ask_to_join_camp', 'camp': camp_id}):
		return False
	
	return True

def desires_weapon(life):
	if not combat.get_weapons(life):
		return True
	
	#if life['stats']['firearms'] >= 5:
	return False

def battle_cry(life):
	_battle_cry = lfe.execute_raw(life, 'talk', 'battle_cry')
	
	if _battle_cry == 'action':
		_battle_cry_action = lfe.execute_raw(life, 'talk', 'battle_cry_action')
		
		lfe.say(life, _battle_cry_action, action=True)

def get_firearm_accuracy(life):
	return numbers.clip((life['stats']['firearms'])/10.0, 0.1, 1)

def get_recoil_recovery_rate(life):
	return numbers.clip(life['stats']['firearms']/10.0, 0.4, 1)

def get_antisocial_percentage(life):
	return life['stats']['introversion']/float(MAX_INTROVERSION)

def get_minimum_group_score(life):
	if life['group']:
		return judgement.judge_group(life, life['group'])
	
	return 0

def get_employability(life):
	#TODO: Placeholder
	return 50

def get_group_motive(life):
	if life['stats']['motive_for_crime'] >= 6:
		if life['stats']['motive_for_wealth'] >= 5:
			return 'wealth'
		
		return 'crime'
	
	if life['stats']['motive_for_wealth'] >= 5:
		return 'wealth'
	
	return 'survival'

def get_influence_from(life, life_id):
	judgement._calculate_impressions(life, life_id)
	_target = LIFE[life_id]
	_know = brain.knows_alife_by_id(life, life_id)
	_score = 0
	
	if life['group'] and life['group'] == _target['group']:
		_group = groups.get_group(life['group'])
		
		if _group['leader'] == _target['id']:
			_power = _know['trust']+_know['danger']
			
			if judgement.can_trust(life, life_id):
				_score += _power
			else:
				_score -= _power
	
	_score += _target['stats']['charisma']
	
	return numbers.clip(_score*2, 0, MAX_INFLUENCE_FROM-((10-_target['stats']['patience'])*8))

def get_minimum_camp_score(life):
	if life['group'] and groups.is_leader(life['group'], life['id']):
		return len(groups.get_group(life['group'])['members'])
	
	return 3

def wants_group_member(life, life_id):
	if not life['group']:
		return False
	
	if not groups.is_leader(life['group'], life['id']):
		return False
	
	_know = brain.knows_alife_by_id(life, life_id)
	if not _know:
		return False
	
	#TODO: Second chance?
	if brain.get_alife_flag(life, life_id, 'invited_to_group'):
		return False
	
	if not lfe.execute_raw(life, 'group', 'wants_group_member', life_id=life_id):
		print 'group not compat'
		return False
	
	return True

def will_obey(life, life_id):
	_know = brain.knows_alife_by_id(life, life_id)
	
	if not _know:
		return False
	
	if judgement.can_trust(life, life_id):
		return True
	
	return False

def can_talk_to(life, life_id):
	if not lfe.execute_raw(life, 'talk', 'can_talk_to', life_id=life_id):
		return False
	
	return True

def can_camp(life):
	if not lfe.execute_raw(life, 'camp', 'can_camp'):
		return False
	
	return True

def can_create_camp(life):
	if not lfe.execute_raw(life, 'camp', 'can_create_camp'):
		return False
	
	return True

def can_bite(life):
	_melee_limbs = lfe.get_melee_limbs(life)
	
	if not _melee_limbs:
		return False
	
	for limb in _melee_limbs:
		if 'CAN_BITE' in lfe.get_limb(life, limb)['flags']:
			return limb
	
	return None

def can_scratch(life):
	_melee_limbs = lfe.get_melee_limbs(life)
	
	if not _melee_limbs:
		print life['name'],'no melee limbs'
		return False
	
	for limb in _melee_limbs:
		if 'SHARP' in lfe.get_limb(life, limb)['flags']:
			return limb
	
	print life['name'],'cant scratch'
	
	return None

def is_nervous(life, life_id):
	if not lfe.execute_raw(life, 'judge', 'nervous', life_id=life_id):
		return False
	
	_dist = numbers.distance(life['pos'], LIFE[life_id]['pos'])
	
	if _dist <= sight.get_vision(LIFE[life_id])/2:
		return True
	
	return False

def is_aggravated(life, life_id):
	if lfe.execute_raw(life, 'judge', 'aggravated', life_id=life_id):
		return True
	
	return False

def is_incapacitated(life):
	_size = sum([lfe.get_limb(life, l)['size'] for l in life['body']])
	_count = 0
	
	for limb in life['body']:
		_count += lfe.limb_is_cut(life, limb)
		_count += lfe.limb_is_in_pain(life, limb)
	
	if (_count/float(_size))>=.35:
		return True
	
	return False

def is_intimidated_by(life, life_id):
	if lfe.execute_raw(life, 'safety', 'intimidated', life_id=life_id):
		return True
	
	return False

def is_intimidated(life):
	for target_id in judgement.get_targets(life, ignore_escaped=True):
		if is_intimidated_by(life, target_id):
			return True
	
	for target_id in judgement.get_combat_targets(life, ignore_escaped=True):
		if is_intimidated_by(life, target_id):
			return True
	
	return False

def is_confident(life):
	#First we'll take a look at the environment
	#Friendlies should be in some state of combat to be a positive influence
	#Enemies will be looked at in terms of their observed health
	_friendlies = []
	_targets = []
	_total_friendly_score = judgement.get_ranged_combat_rating_of_self(life)
	_total_enemy_score = 0
	
	#Who do we like? Where are they?
	#Let's find these and then generate a "safety map"
	for target_id in judgement.get_trusted(life, visible=False):
		_knows = brain.knows_alife_by_id(life, target_id)
		
		if _knows:
			if _knows['last_seen_time'] > 100:
				continue
			
			if numbers.distance(life['pos'], _knows['last_seen_at'])<sight.get_vision(life):
				_friendlies.append(target_id)
				
				_zones = [zones.get_zone_at_coords(life['pos'])]
				_z = zones.get_zone_at_coords(_knows['last_seen_at'])
				
				if not _z in _zones:
					_zones.append(_z)
				
				_distance = zones.dijkstra_map(life['pos'], [_knows['last_seen_at']], _zones, return_score=True)
				_distance = numbers.clip(_distance, 0, 100)
				
				_combat_rating = judgement.get_ranged_combat_rating_of_target(life, target_id)
				if _knows['last_seen_time']:
					_distance = numbers.clip(_distance+_knows['last_seen_time'], 0, 100)
					
				_score = _combat_rating*((100-_distance+_combat_rating)/100.0)
				
				_total_friendly_score += numbers.clip(_score, 0, _combat_rating)
	
	for target_id in judgement.get_combat_targets(life):
		_knows = brain.knows_alife_by_id(life, target_id)
		
		if _knows and _knows['last_seen_time'] <= 200:
			if numbers.distance(life['pos'], _knows['last_seen_at'])<sight.get_vision(life):
				_targets.append(target_id)
				
				_zones = [zones.get_zone_at_coords(life['pos'])]
				_z = zones.get_zone_at_coords(_knows['last_seen_at'])
				
				if not _z in _zones:
					_zones.append(_z)
				
				_distance = zones.dijkstra_map(life['pos'], [_knows['last_seen_at']], _zones, return_score=True)
				_distance = numbers.clip(_distance, 0, 100)
				
				_combat_rating = judgement.get_ranged_combat_rating_of_target(life, target_id)
				if _knows['last_seen_time']:
					_distance = numbers.clip(_distance+_knows['last_seen_time'], 0, 100)
					
				_score = _combat_rating*((100-_distance+_combat_rating)/100.0)
				
				_total_enemy_score += numbers.clip(_score, 0, _combat_rating)
				#_z = zones.get_zone_at_coords(_knows['last_seen_at'])
				#if not _z in _f_zones:
				#	_f_zones.append(_z)
	
	if _total_friendly_score>=_total_enemy_score:
		return True
	
	return False

def is_combat_target_too_close(life):
	_nearest_combat_target = judgement.get_nearest_combat_target(life)
	
	_knows = brain.knows_alife_by_id(life, _nearest_combat_target['target_id'])
	
	if not _nearest_combat_target['target_id']:
		return False
	
	if _knows['last_seen_time'] >= 100:
		return False
	
	#TODO: Unhardcode
	if _nearest_combat_target['distance'] <= 10:
		return True
	
	return False

def is_same_species(life, life_id):
	if life['species'] == LIFE[life_id]['species']:
		return True
	
	return False

def is_family(life, life_id):
	_know = brain.knows_alife_by_id(life, life_id)
	
	if not _know:
		return False
	
	for relation in ['son', 'daughter', 'mother', 'father', 'sibling']:
		if brain.get_alife_flag(life, life_id, relation):
			return True
	
	return False

def is_child_of(life, life_id):
	_know = brain.knows_alife_by_id(life, life_id)

	if not _know:
		return False
	
	if not _know['escaped'] and _know['life']['dead']:
		return False
	
	for relation in ['mother', 'father']:
		if brain.get_alife_flag(life, life_id, relation):
			return True
	
	return False

def is_parent_of(life, life_id):
	_know = brain.knows_alife_by_id(life, life_id)
	
	if not _know:
		return False
	
	for relation in ['son', 'daughter']:
		if brain.get_alife_flag(life, life_id, relation):
			return True
	
	return False

def has_parent(life):
	for life_id in life['know'].keys():
		if is_child_of(life, life_id):
			return True
	
	return False

def has_child(life):
	for life_id in life['know'].keys():
		if is_parent_of(life, life_id):
			return True
	
	return False

def is_safe_in_shelter(life, life_id):
	if not lfe.is_in_shelter(life):
		return True
	
	if not is_compatible_with(life, life_id):
		return False
	
	return True

def is_compatible_with(life, life_id):
	_diff = MAX_CHARISMA-abs(life['stats']['charisma']-LIFE[life_id]['stats']['charisma'])	
	
	#I don't trust modders with this
	if not is_same_species(life, life_id):
		return False
	
	#print _diff, life['stats']['sociability']
	if _diff <= life['stats']['sociability']:
		return True
	
	#TODO: Hardcoded
	if judgement.get_trust(life, life_id)>=5:
		return True
	
	return False

def is_target_group_friendly(life, life_id):
	_target = LIFE[life_id]
	
	#Different groups
	if _target['group'] and not _target['group'] == life['group']:
		if life['group']:
			_motive = groups.get_motive(life['group'])
			
			if _motive == 'crime':
				return False
			
			if _motive == 'survival' and judgement.is_group_hostile(life, _target['group']):
				return False
		else:
			if judgement.is_group_hostile(life, _target['group']):
				return False
		
	return True
	#if life['group']:
	#((life['group'] and groups.is_member(life['group'], life_id)) or (not LIFE[life_id]['group'] or not life['group']))==True

def is_born_leader(life):
	return life['stats']['is_leader']

def _has_attacked(life, life_id, target_list):
	for memory in lfe.get_memory(life, matches={'text': 'heard about attack', 'attacker': life_id}):
		if memory['target'] in target_list:
			return True
	
	return False

def has_attacked_trusted(life, life_id):
	return _has_attacked(life, life_id, judgement.get_trusted(life))

def distance_from_pos_to_pos(life, pos1, pos2):
	return numbers.distance(pos1, pos2)
