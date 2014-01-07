from globals import *

import life as lfe

import historygen
import judgement
import survival
import speech
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

def desires_first_contact_with(life, life_id):
	#print life['name'], LIFE[life_id]['name'],brain.knows_alife_by_id(life, life_id)['alignment']
	if not brain.knows_alife_by_id(life, life_id)['alignment'] == 'neutral':
		return False
	
	if life['group'] and not groups.is_leader(life, life['group'], life['id']):
		#Don't talk if we're in a group and near our leader.
		#TODO: #judgement Even then, we should consider having group members avoid non-members regardless.
		#TODO: #judgement How do group types play into this?
		_leader = brain.knows_alife_by_id(life, groups.get_leader(life, life['group']))
		
		if _leader:
			#TODO: #judgement Placeholder for future logic.
			if numbers.distance(life['pos'], _leader['life']['pos']) < 100:
				return False
	
	if life['stats']['motive_for_crime']>=4:
		return True
	
	if life['stats']['sociability']>=6:
		return True
	
	return False

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

def wants_to_abandon_group(life, group_id):
	_trusted = 0
	_hostile = 0
	
	for member in groups.get_group_memory(life, group_id, 'members'):
		if life['id'] == member:
			continue
		
		_knows = brain.knows_alife_by_id(life, member)
		
		if _knows['alignment'] == 'hostile':
			_hostile += 1
		else:
			_trusted += 1
	
	return _hostile>_trusted

def desires_group(life, group_id):
	if life['group']:
		return wants_to_abandon_group(life, life['group'], with_new_group_in_mind=group_id)
	
	if judgement.judge_group(life, group_id)>get_minimum_group_score(life):
		return True
	
	return False

def desires_to_create_camp(life):
	if not 'CAN_GROUP' in life['life_flags']:
		return False
		
	if life['group'] and not groups.get_camp(life['group']) and groups.is_leader(life, life['group'], life['id']):
		if len(groups.get_group(life, life['group'])['members'])>1:
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

def get_melee_skill(life):
	return numbers.clip((life['stats']['melee'])/10.0, 0.1, 1)

def get_firearm_accuracy(life):
	return numbers.clip((life['stats']['firearms'])/10.0, 0.35, 1)

def get_recoil_recovery_rate(life):
	return numbers.clip(life['stats']['firearms']/10.0, 0.4, 1)*.4

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

def get_minimum_camp_score(life):
	if life['group'] and groups.is_leader(life, life['group'], life['id']):
		return len(groups.get_group(life, life['group'])['members'])
	
	return 3

def wants_group_member(life, life_id):
	if not life['group']:
		return False
	
	if groups.is_member(life, life['group'], life_id):
		return False
	
	if not groups.is_leader(life, life['group'], life['id']):
		return False
	
	if not lfe.execute_raw(life, 'group', 'wants_group_member', life_id=life_id):
		return False
	
	_know = brain.knows_alife_by_id(life, life_id)
	if not _know:
		return False
	
	if not judgement.can_trust(life, life_id):
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
	if LIFE[life_id]['asleep'] or LIFE[life_id]['dead']:
		return False
		
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
		_count += lfe.get_limb_pain(life, limb)
	
	if (_count/float(_size))>=.35:
		return True
	
	return False

def is_intimidated_by(life, life_id):
	if lfe.execute_raw(life, 'safety', 'intimidated', life_id=life_id):
		return True
	
	return False

def is_intimidated(life):
	#for target_id in judgement.get_targets(life, ignore_escaped=True):
	#	if is_intimidated_by(life, target_id):
	#		return True
	
	for target_id in judgement.get_threats(life, ignore_escaped=True):
		if is_intimidated_by(life, target_id):
			return True
	
	return False

def is_confident(life):
	_friendly_confidence = 0
	_threat_confidence = 0
	
	for target_id in judgement.get_trusted(life, visible=False):
		_knows = brain.knows_alife_by_id(life, target_id)
		
		if _knows['dead'] or _knows['asleep']:
			continue
		
		_recent_mod = numbers.clip(_knows['last_seen_time'], 0, 300)/300.0
		
		if _knows['last_seen_time']:
			_friendly_confidence += _recent_mod
		else:
			_friendly_confidence += judgement.get_ranged_combat_rating_of_target(life, target_id)*_recent_mod
	
	for target_id in judgement.get_threats(life, ignore_escaped=True):
		_knows = brain.knows_alife_by_id(life, target_id)
		
		if _knows['dead'] or _knows['asleep']:
			continue
		
		_recent_mod = numbers.clip(_knows['last_seen_time'], 0, 300)/300.0
		
		if _knows['last_seen_time']:
			_threat_confidence += 2*_recent_mod
		else:
			_threat_confidence += judgement.get_ranged_combat_rating_of_target(life, target_id)*_recent_mod
	
	return _friendly_confidence > _threat_confidence

def is_threat_too_close(life):
	_nearest_threat = judgement.get_nearest_threat(life)
	
	_knows = brain.knows_alife_by_id(life, _nearest_threat)
	
	if not _nearest_threat:
		return False
	
	if _knows['last_seen_time'] >= 100:
		return False
	
	_danger_close_range = int(lfe.execute_raw(life, 'safety', 'danger_close_range'))
	if numbers.distance(life['pos'], _knows['last_seen_at'])<_danger_close_range:
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
	
	return True

def is_born_leader(life):
	return life['stats']['is_leader']

def is_psychotic(life):
	return life['stats']['psychotic']

def _has_attacked(life, life_id, target_list):
	for memory in lfe.get_memory(life, matches={'text': 'heard about attack', 'attacker': life_id}):
		if memory['target'] in target_list:
			return True
	
	return False

def has_attacked_trusted(life, life_id):
	return _has_attacked(life, life_id, judgement.get_trusted(life))

def has_attacked_self(life, life_id):
	return len(lfe.get_memory(life, matches={'text': 'shot_by', 'target': life_id}))>0

def react_to_attack(life, life_id):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	if not _knows['alignment'] == 'hostile':
		speech.start_dialog(life, _knows['life']['id'], 'establish_hostile')
		
	if life['group']:
		groups.announce(life, life['group'], 'attacked_by_hostile', target_id=_knows['life']['id'])

def react_to_tension(life, life_id):
	if brain.knows_alife_by_id(life, life_id)['alignment'] in ['hostile']:
		return False
	
	if life['group'] and not groups.is_leader(life, life['group'], life['id']) and groups.get_leader(life, life['group']):
		if sight.can_see_target(life, groups.get_leader(life, life['group'])) and sight.can_see_target(LIFE[life_id], groups.get_leader(life, life['group'])):
			return False
	
	_disarm = brain.get_alife_flag(life, life_id, 'disarm')
	
	if _disarm:
		#For now...
		if not sight.can_see_position(life, LIFE[life_id]['pos']):
			groups.announce(life, life['group'], 'attacked_by_hostile', target_id=life_id)
			
			return False
		
		for item_uid in lfe.get_all_visible_items(LIFE[life_id]):
			if ITEMS[item_uid]['type'] == 'gun':
				break
		else:
			brain.unflag_alife(life, life_id, 'disarm')
			speech.start_dialog(life, life_id, 'clear_drop_weapon')
			
			return False
		
		_time_elapsed = WORLD_INFO['ticks']-_disarm
		
		if _time_elapsed>135 and not speech.has_sent(life, life_id, 'threaten'):
			speech.start_dialog(life, life_id, 'threaten')
			speech.send(life, life_id, 'threaten')
		elif _time_elapsed>185:
			speech.start_dialog(life, life_id, 'establish_hostile')
	elif not speech.has_sent(life, life_id, 'confront'):
		speech.start_dialog(life, life_id, 'confront')
		speech.send(life, life_id, 'confront')

def distance_from_pos_to_pos(life, pos1, pos2):
	return numbers.distance(pos1, pos2)

def get_goal_alignment_for_target(life, life_id):
	_genuine = 100
	_malicious = 100
	
	if is_psychotic(life):
		if life['group']:
			if not life['group'] == LIFE[life_id]['group']:
				return 'hostile'
		else:
			return 'hostile'
	
	_malicious*=life['stats']['motive_for_crime']/10.0	
	
	if life['stats']['lone_wolf']:
		_malicious*=.65
		_genuine*=.65
	
	if life['stats']['self_absorbed']:
		_malicious*=.85
	
	if not _genuine>=50 and not _malicious>=50:
		return False
	
	if _malicious>=75 and _genuine>=75:
		return 'feign_trust'
	
	if _genuine>_malicious:
		return 'trust'
	
	return 'hostile'

def change_alignment(life, life_id, alignment):
	_knows = brain.knows_alife_by_id(life, life_id)
	
	if not _knows:
		brain.meet_alife(life, LIFE[life_id])
		_knows = brain.knows_alife_by_id(life, life_id)
	
	logging.debug('%s changed alignment of %s: %s' % (' '.join(life['name']), ' '.join(LIFE[life_id]['name']), alignment))
	_knows['alignment'] = alignment

def establish_trust(life, life_id):
	change_alignment(life, life_id, 'trust')

def establish_feign_trust(life, life_id):
	change_alignment(life, life_id, 'feign_trust')

def establish_aggressive(life, life_id):
	change_alignment(life, life_id, 'aggressive')

def establish_hostile(life, life_id):
	change_alignment(life, life_id, 'hostile')

def establish_scared(life, life_id):
	change_alignment(life, life_id, 'scared')

def declare_group_target(life, target_id, alignment):
	change_alignment(life, target_id, alignment)
	
	groups.announce(life, life['group'], 'add_group_target', target_id=target_id)

def declare_group(life, group_id, alignment):
	groups.update_group_memory(life, group_id, 'alignment', alignment)
	
	for member in groups.get_group_memory(life, group_id, 'members'):
		change_alignment(life, member, alignment)
	
	logging.debug('%s declared group %s %s.' % (' '.join(life['name']), group_id, alignment))

def declare_group_trusted(life, group_id):
	declare_group(life, group_id, 'trust')

def declare_group_hostile(life, group_id):
	declare_group(life, group_id, 'hostile')

def declare_group_scared(life, group_id):
	declare_group(life, group_id, 'scared')