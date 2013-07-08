from globals import *

import life as lfe

import judgement
import groups
import sight
import brain

import numbers
import logging
import random

MAX_INFLUENCE_FROM = 75
MAX_WILLPOWER = 25
MAX_INTROVERSION = 10
MAX_SOCIABILITY = 25
MAX_INTERACTION = 25
MAX_CHARISMA = 20

def init(life):
	life['stats']['willpower'] = random.randint(1, MAX_WILLPOWER)
	life['stats']['sociability'] = random.randint(15, MAX_SOCIABILITY)
	life['stats']['introversion'] = random.randint(1, MAX_INTROVERSION)
	life['stats']['charisma'] = random.randint(1, MAX_CHARISMA)

def desires_job(life):
	_wont = brain.get_flag(life, 'wont_work')
	if life['job'] or _wont:
		if _wont:
			_wont = brain.flag(life, 'wont_work', value=_wont-1)
			
		return False
	
	if life['stats']['willpower']>random.randint(0, MAX_WILLPOWER-(life['stats']['willpower']/2)):
		return True
	
	brain.flag(life, 'wont_work', value=1000-(life['stats']['willpower']*15))
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
	
	if life['stats']['willpower'] >= MAX_WILLPOWER*.5:
		return True
	
	return False

def wants_to_abandon_group(life, group_id, with_new_group_in_mind=None):
	if with_new_group_in_mind:
		if judgement.judge_group(life, with_new_group_in_mind)>get_minimum_group_score(life):
			return True
	
	_group = groups.get_group(group_id)
	if WORLD_INFO['ticks']-_group['time_created']<life['stats']['willpower']+life['stats']['sociability']:
		return False
	
	_top_group = {'id': -1, 'score': 0}
	for memory in lfe.get_memory(life, matches={'group': '*'}):
		if not memory['group'] in GROUPS:
			continue
		
		_score = 0
		
		if 'trust' in memory:
			_score += memory['trust']
		
		if 'danger' in memory:
			_score += memory['danger']
	
		if _score > _top_group['score'] or _top_group['id'] == -1:
			_top_group['id'] = memory['group']
			_top_group['score'] = _score
		
	if _top_group:
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

def desires_camp(life):
	print 'Dead code'
	return False

def get_antisocial_percentage(life):
	return life['stats']['introversion']/float(MAX_INTROVERSION)

def get_minimum_group_score(life):
	if life['group']:
		return judgement.judge_group(life, life['group'])
	
	return 0

def get_max_group_size(life):
	return int(round(life['stats']['sociability']*get_antisocial_percentage(life)))

def get_employability(life):
	#TODO: Placeholder
	return 50

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
	
	return numbers.clip(_score*2, 0, MAX_INFLUENCE_FROM-(MAX_WILLPOWER-_target['stats']['willpower']))

def get_minimum_camp_score(life):
	if life['group'] and groups.is_leader(life['group'], life['id']):
		return len(groups.get_group(life['group'])['members'])
	
	return 3

def wants_group_member(life, life_id):
	if not life['group']:
		return False
	
	if not groups.is_leader(life['group'], life['id']):
		return False
	
	_group = groups.get_group(life['group'])
	if len(_group['members'])>get_max_group_size(life):
		return False
	
	_know = brain.knows_alife_by_id(life, life_id)
	if not _know:
		return False
	
	#TODO: Second chance?
	if brain.get_alife_flag(life, _know['life'], 'invited_to_group'):
		return False
	
	if not lfe.execute_raw(life, 'group', 'wants_group_member', life_id=life_id):
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
	if is_same_species(life, life_id):
		return False
	
	_dist = numbers.distance(life['pos'], LIFE[life_id]['pos'])
	
	if _dist <= sight.get_vision(LIFE[life_id])/2:
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
	
	for relation in ['son', 'daughter', 'mother', 'father']:
		if brain.get_alife_flag(life, _know['life'], relation):
			return True
	
	return False

def is_compatible_with(life, life_id):
	_diff = MAX_CHARISMA-abs(life['stats']['charisma']-LIFE[life_id]['stats']['charisma'])
	
	#I don't trust modders with this
	if not is_same_species(life, life_id):
		print 'NO TRUST'
		return False
	
	if _diff < life['stats']['sociability']:
		return True
	
	print _diff,life['stats']['sociability']
	return False

def has_attacked_trusted(life, life_id):
	_trusted = judgement.get_trusted(life)
	
	for memory in lfe.get_memory(life, matches={'text': 'heard about attack', 'attacker': life_id}):
		if memory['target'] in _trusted:
			print 'HAS ATTACKED TRUSTED' * 10
			return True
	
	return False
