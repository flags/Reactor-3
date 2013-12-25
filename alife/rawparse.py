from globals import *

import life as lfe

import alife_manage_items
import alife_discover
import alife_shelter
import alife_search
import alife_combat
import alife_follow
import alife_cover
import alife_needs
import alife_hide

import references
import judgement
import survival
import movement
import logging
import numbers
import memory
import groups
import combat
import chunks
import speech
import dialog
import brain
import items
import stats
import logic
import sight
import jobs

import re

CURLY_BRACE_MATCH = '{[\w+-=\.,]*}'

def create_function_map():
	FUNCTION_MAP.update({'is_family': stats.is_family,
		'is_same_species': stats.is_same_species,
		'can_trust': judgement.can_trust,
		'is_dangerous': judgement.is_target_dangerous,
		'can_bite': stats.can_bite,
		'can_scratch': stats.can_scratch,
		'weapon_equipped_and_ready': combat.weapon_equipped_and_ready,
		'prepare_for_ranged': combat.prepare_for_ranged,
		'explore_unknown_chunks': survival.explore_unknown_chunks,
		'is_nervous': stats.is_nervous,
		'is_aggravated': stats.is_aggravated,
		'is_scared': judgement.is_scared,
		'is_safe': judgement.is_safe,
		'is_healthy': None,
		'is_intimidated': stats.is_intimidated,
		'is_intimidating': lambda life, life_id: stats.is_intimidated_by(LIFE[life_id], life['id']),
		'is_confident': stats.is_confident,
		'is_situation_tense': lambda life: judgement.get_tension(life)>=10,
		'is_combat_ready': lambda life, life_id: not LIFE[life_id]['state'] in ['hiding', 'hidden'],
		'is_surrendering': lambda life, life_id: LIFE[life_id]['state'] == 'surrender',
		'is_being_surrendered_to': lambda life: len(judgement.get_combat_targets(life, ignore_escaped=True, filter_func=lambda life, life_id: LIFE[life_id]['state'] == 'surrender'))>0,
		'closest': None,
		'kill': lambda life: lfe.kill(life, 'their own dumb self'),
		'has_attacked_trusted': stats.has_attacked_trusted,
		'has_attacked_self': stats.has_attacked_self,
		'distance_to_pos': stats.distance_from_pos_to_pos,
		'current_chunk_has_flag': lambda life, flag: chunks.get_flag(life, lfe.get_current_chunk_id(life), flag)>0,
		'is_idle': lambda life: life['state'] == 'idle',
		'is_relaxed': lambda life: life['state_tier'] == TIER_RELAXED,
		'is_child_of': stats.is_child_of,
		'is_parent_of': stats.is_parent_of,
		'has_parent': stats.has_parent,
		'has_child': stats.has_child,
		'is_night': logic.is_night,
		'is_born_leader': stats.is_born_leader,
		'is_psychotic': stats.is_psychotic,
		'is_safe_in_shelter': stats.is_safe_in_shelter,
		'is_incapacitated': stats.is_incapacitated,
		'is_target': lambda life, life_id: life_id in judgement.get_targets(life) or life_id in judgement.get_combat_targets(life),
		'seen_target_recently': lambda life, life_id: brain.knows_alife_by_id(life, life_id)['last_seen_time']<=150,
		'is_combat_target': lambda life, life_id: life_id in judgement.get_combat_targets(life),
		'is_traitor': lambda life, life_id: len(lfe.get_memory(life, matches={'text': 'traitor', 'target': life_id}))>0,
		'is_awake': judgement.is_target_awake,
		'is_dead': judgement.is_target_dead,
		'is_raiding': lambda life: life['group'] and groups.get_stage(life, life['group'])==STAGE_RAIDING,
		'find_and_announce_shelter': groups.find_and_announce_shelter,
		'desires_shelter': stats.desires_shelter,
		'travel_to_position': movement.travel_to_position,
		'find_target': movement.find_target,
		'can_see_target': sight.can_see_target,
		'has_threats': lambda life: len(judgement.get_threats(life, ignore_escaped=1))>0,
		'has_visible_threat': lambda life: len(judgement.get_visible_threats(life))>0,
		'has_combat_targets': lambda life: len(judgement.get_combat_targets(life))>0,
		'has_lost_threat': lambda life: len(judgement.get_threats(life, escaped_only=True, ignore_escaped=2))>0,
		'has_ready_combat_targets': lambda life: len(judgement.get_ready_combat_targets(life, recent_only=True, limit_distance=sight.get_vision(life)+10))>0,
		'danger_close': stats.is_threat_too_close,
		'number_of_alife_in_chunk_matching': lambda life, chunk_key, matching, amount: len(chunks.get_alife_in_chunk_matching(chunk_key, matching))>amount,
		'number_of_alife_in_reference_matching': lambda life, reference_id, matching, amount: len(references.get_alife_in_reference_matching(reference_id, matching))>amount,
		'announce_to_group': groups.announce,
		'is_in_chunk': chunks.is_in_chunk,
		'is_in_shelter': lfe.is_in_shelter,
		'has_shelter': lambda life: len(judgement.get_known_shelters(life))>0,
		'has_completed_job': lambda life, job_id: job_id in life['completed_jobs'],
		'has_completed_task': lambda life, job_id: job_id in life['completed_jobs'],
		'retrieve_from_memory': brain.retrieve_from_memory,
		'pick_up_and_hold_item': lfe.pick_up_and_hold_item,
		'has_usable_weapon': lambda life: not combat.has_ready_weapon(life) == True,
		'target_is_combat_ready': judgement.target_is_combat_ready,
		'create_item_need': survival.add_needed_item,
		'group_needs_resources': lambda life, group_id: groups.needs_resources(group_id),
		'has_needs_to_meet': survival.has_needs_to_meet,
		'has_unmet_needs': survival.has_unmet_needs,
		'has_needs_to_satisfy': survival.has_needs_to_satisfy,
		'has_needs': lambda life: survival.has_needs_to_meet(life) or survival.has_unmet_needs(life) or survival.has_needs_to_satisfy(life),
		'has_number_of_items_matching': lambda life, matching, amount: len(lfe.get_all_inventory_items(life, matches=matching))>=amount,
		'flag_item_matching': lambda life, matching, flag: lfe.get_all_inventory_items(life, matches=[matching]) and brain.flag_item(life, lfe.get_all_inventory_items(life, matches=[matching])[0], flag)>0,
		'drop_item_matching': lambda life, matching: lfe.get_all_inventory_items(life, matches=[matching]) and lfe.drop_item(life, lfe.get_all_inventory_items(life, matches=[matching])[0]['uid'])>0,
		'has_target_to_follow': lambda life: judgement.get_target_to_follow(life)>0,
		'has_target_to_guard': lambda life: judgement.get_target_to_guard(life)>0,
		'get_recent_events': speech.get_recent_events,
		'get_target': lambda life, life_id: speech.get_target(life,
	                                                           lfe.has_dialog_with(life, life_id),
	                                                           dialog.get_flag(lfe.has_dialog_with(life, life_id),
	                                                                           'NEXT_GIST')),
		'get_needs': lambda life, life_id: speech.get_needs(life,
	                                                         lfe.has_dialog_with(life, life_id),
	                                                         dialog.get_flag(lfe.has_dialog_with(life, life_id),
	                                                                         'NEXT_GIST')),
		'get_location': lambda life: '%s, %s' % (life['pos'][0], life['pos'][1]),
		'join_group': lambda life, **kwargs: groups.join_group(life, kwargs['group_id']),
		'add_group_member': lambda life, life_id: groups.add_member(life, life['group'], life_id),
		'claim_to_be_group_leader': lambda life, life_id: groups.set_leader(life, life['group'], life['id']),
		'is_group_leader': lambda life: groups.is_leader_of_any_group(life)==True,
		'is_in_same_group': lambda life, life_id: (life['group'] and LIFE[life_id]['group'] == life['group'])>0,
		'is_target_group_leader': lambda life, life_id: (groups.is_leader_of_any_group(LIFE[life_id]))==True,
		'is_in_group': lambda life: life['group']>0,
		'is_target_hostile': lambda life, life_id: brain.knows_alife_by_id(life, life_id)['alignment'] == 'hostile',
		'is_target_in_group': lambda life, life_id, **kwargs: brain.knows_alife_by_id(life, life_id)['group']==kwargs['group'],
		'is_target_in_any_group': lambda life, life_id: brain.knows_alife_by_id(life, life_id)['group']>0,
		'is_target_group_friendly': lambda life, life_id: brain.knows_alife_by_id(life, life_id)['group'] and groups.get_group_memory(life, brain.knows_alife_by_id(life, life_id)['group'], 'alignment')=='trust',
		'is_target_group_hostile': lambda life, life_id: brain.knows_alife_by_id(life, life_id)['group'] and groups.get_group_memory(life, brain.knows_alife_by_id(life, life_id)['group'], 'alignment')=='hostile',
		'is_target_group_neutral': lambda life, life_id: brain.knows_alife_by_id(life, life_id)['group'] and groups.get_group_memory(life, brain.knows_alife_by_id(life, life_id)['group'], 'alignment')=='neutral',
		'is_group_hostile': lambda life, **kwargs: groups.get_group_memory(life, kwargs['group_id'], 'alignment')=='hostile',
		'inform_of_group_members': speech.inform_of_group_members,
		'update_group_members': speech.update_group_members,
		'get_group_flag': groups.get_flag,
		'get_flag': brain.get_flag,
		'get_group': lambda life: life['group'],
		'discover_group': lambda life, **kwargs: groups.discover_group(life, kwargs['group_id']),
		'add_target_to_known_group': lambda life, life_id, **kwargs: groups.add_member(life, kwargs['group_id'], life_id),
		'knows_about_group': lambda life, **kwargs: groups.group_exists(life, kwargs['group_id']),
		'group_has_shelter': lambda life: groups.get_shelter(life, life['group'])>0,
		'declare_group_hostile': lambda life, **kwargs: stats.declare_group_hostile(life, kwargs['group_id']),
		'declare_group_trusted': lambda life, **kwargs: stats.declare_group_trusted(life, kwargs['group_id']),
		'declare_group_target': lambda life, life_id: stats.declare_group_target(life, life_id, 'hostile'),
		'get_group_shelter': lambda life: groups.get_shelter(life, life['group']),
		'set_group_shelter': lambda life, **kwargs: groups.set_shelter(life, kwargs['group_id'], kwargs['shelter']),
		'get_group_stage': lambda life: groups.get_stage(life, life['group']),
		'get_group_stage_message': speech.get_group_stage_message,
		'set_group_stage': lambda life, **kwargs: groups.set_stage(life, kwargs['group_id'], kwargs['stage']),
		'is_group_motivated_for_crime': lambda life: life['group'] and groups.get_motive(life, life['group']) == 'crime',
		'wants_to_leave_group_for_group': lambda life: stats.wants_to_abandon_group(life, life['group']),
		'knows_items_matching': lambda life, **kwargs: len(brain.get_multi_matching_remembered_items(life, kwargs['items'], no_owner=True))>0,
		'get_known_group': speech.get_known_group,
		'inform_of_group': speech.inform_of_group,
		'force_inform_of_group': speech.force_inform_of_group,
		'inform_of_items': lambda life, life_id, **kwargs: speech.inform_of_items(life, life_id, kwargs['items']),
		'update_location': lambda life, life_id: brain.update_known_life(life, life_id, 'last_seen_at', life['pos'][:]),
		'has_questions_for_target': lambda life, life_id: len(memory.get_questions_for_target(life, life_id))>0,
		'has_orders_for_target': lambda life, life_id: len(memory.get_orders_for_target(life, life_id))>0,
		'ask_target_question': memory.ask_target_question,
		'give_target_order_message': memory.give_target_order_message,
		'give_target_order': memory.give_target_order,
		'take_order': memory.take_order,
		'reject_order': memory.reject_order,
		'get_introduction_message': speech.get_introduction_message,
		'get_introduction_gist': speech.get_introduction_gist,
		'establish_trust': stats.establish_trust,
		'establish_feign_trust': stats.establish_trust,
		'establish_aggressive': stats.establish_aggressive,
		'establish_hostile': stats.establish_hostile,
		'establish_scared': stats.establish_scared,
		'claim_hostile': lambda life, target, **kwargs: stats.establish_hostile(life, kwargs['target_id']),
		'describe_target': lambda life, life_id, **kwargs: speech.describe_target(life, kwargs['target']),
		'consume': lfe.consume,
		'explode': items.explode,
		'is_player': lambda life: 'player' in life,
		'is_neutral': lambda life, life_id: brain.knows_alife_by_id(life, life_id)['alignment'] == 'neutral',
		'reset_think_timer': lfe.reset_think_rate,
		'mark_target_as_combat_ready': lambda life, life_id: brain.flag_alife(life, life_id, 'combat_ready'),
		'mark_target_as_not_combat_ready': lambda life, life_id: brain.flag_alife(life, life_id, 'combat_ready', value=False),
		'saw_target_recently': lambda life, **kwargs: brain.knows_alife_by_id(life, kwargs['target_id']) and -1<brain.knows_alife_by_id(life, kwargs['target_id'])['last_seen_time']<6000,
		'update_location_of_target_from_target': speech.update_location_of_target_from_target,
		'ping': lambda life: logging.debug('%s: Ping!' % ' '.join(life['name'])),
		'wander': lambda life: alife_discover.tick(life),
		'pick_up_item': lambda life: alife_needs.tick(life),
		'take_shelter': lambda life: alife_shelter.tick(life),
		'has_non_relaxed_goal': lambda life: life['state_tier']>TIER_RELAXED,
		'needs_to_manage_inventory': lambda life: alife_manage_items.conditions(life),
		'manage_inventory': lambda life: alife_manage_items.tick(life),
		'cover_exposed': lambda life: len(combat.get_exposed_positions(life))>0,
		'ranged_ready': lambda life: lfe.execute_raw(life, 'combat', 'ranged_ready'),
		'ranged_attack': lambda life: alife_combat.ranged_attack(life),
		'melee_ready': lambda life: lfe.execute_raw(life, 'combat', 'melee_ready'),
		'melee_attack': lambda life: alife_combat.melee_attack(life),
		'take_cover': lambda life: alife_cover.tick(life),
		'hide': lambda life: alife_hide.tick(life),
		'search_for_threat': lambda life: alife_search.tick(life),
		'has_recoil': lambda life: life['recoil']>=4,
		'has_focus_point': lambda life: len(lfe.get_memory(life, matches={'text': 'focus_on_chunk'}))>0,
		'walk_to': lambda life: movement.travel_to_chunk(life, lfe.get_memory(life, matches={'text': 'focus_on_chunk'})[0]['chunk_key']),
		'follow_target': alife_follow.tick,
		'guard_focus_point': lambda life: movement.guard_chunk(life, lfe.get_memory(life, matches={'text': 'focus_on_chunk'})[0]['chunk_key']),
		'get_id': lambda life: life['id'],
		'always': lambda life: 1==1,
		'pass': lambda life, *a, **k: True,
		'never': lambda life: 1==2})

def create_rawlangscript():
	return {'section': '', 'sections': {}}

def create_section(script, section):
	script['sections'][section] = {}

def set_active_section(script, section):
	script['section'] = section

def create_action(script, identifier, argument_groups):
	_arg_groups = []
	
	for arguments in argument_groups:
		_args = []
		
		for argument in arguments:
			if argument.count('['):
				bracket_data = [entry.strip('[').strip(']') for entry in re.findall('\[[\w]*\]', argument)]
				curly_BRACE_data = [entry.strip('{').strip('}') for entry in re.findall(CURLY_BRACE_MATCH, argument)]
				_args.append({'function': argument.split('[')[0]})
			else:
				curly_BRACE_data = re.findall(CURLY_BRACE_MATCH, argument)
				
				if curly_BRACE_data:
					argument = [argument.replace(entry, '') for entry in curly_BRACE_data][0]
					curly_BRACE_data = [data.strip('{').strip('}') for data in curly_BRACE_data][0].split(',')
					_arguments = curly_BRACE_data
					_values = []
					
					for value in _arguments:
						_arg = {}
						
						if value.count('.'):
							_arg['target'] = value.partition('.')[0]
							_arg['flag'] = value.partition('.')[2].partition('+')[0].partition('-')[0]
							
							if value.count('+'):
								_arg['value'] = int(value.partition('+')[2])
							elif value.count('-'):
								_arg['value'] = -int(value.partition('-')[2])
						elif value.count('='):
							_arg['key'],_arg['value'] = value.split('=')
						
						_values.append(_arg)
					
				else:
					argument = argument.split('{')[0]
					_values = []
				
				_true = True
				_string = ''
				_self_call = False
				_no_args = False
	
				while 1:
					if argument.startswith('*'):
						argument = argument.replace('*', '')
						_true = '*'
					elif argument.startswith('\"'):
						argument = argument.replace('\"', '')
						_string = argument
					elif argument.startswith('%'):
						argument = argument[1:]
						_no_args = True
					elif argument.startswith('!'):
						argument = argument[1:]
						_true = False
					elif argument.startswith('@'):
						argument = argument[1:]
						_self_call = True
					else:
						break
					
					continue
				
				if _string:
					_args.append({'string': _string})
				else:
					_args.append({'function': translate(argument),
						'values': _values,
						'true': _true,
						'string': None,
						'self_call': _self_call,
						'no_args': _no_args})
		
		_arg_groups.append(_args)
		
	return {'id': identifier, 'arguments': _arg_groups}

def add_action(script, action):
	script['sections'][script['section']][action['id']] = action['arguments']

def parse(script, line, filename='', linenumber=0):
	if not line.count('[') == line.count(']'):
		raise Exception('BRACE mismatch (%s, line %s): %s' % (filename, linenumber, line))
	
	bracket_data = [entry.strip('[').strip(']') for entry in re.findall('\[[\w]*\]', line)]
	
	if line.startswith('['):
		create_section(script, bracket_data[0])
		set_active_section(script, bracket_data[0])
	
	elif script['section'] and line.count(':'):
		_split = line.split(':')
		identifier = _split[0]
		arguments = []
		
		for _argument_group in _split[1].split('|'):
			if _argument_group.rpartition('{')[2].rpartition('}')[0].count(','):
				arguments.append([_argument_group])
			else:
				arguments.append(_argument_group.split(','))
		
		add_action(script, create_action(script, identifier, arguments))

def read(filename):
	_script = create_rawlangscript()
	with open(filename, 'r') as e:
		_i = 1
		for line in e.readlines():
			if line.startswith('#'):
				continue
			
			parse(_script, line.strip().lower(), filename=filename, linenumber=_i)
			_i += 1
	
	return _script

def raw_has_section(life, section):
	if section in life['raw']['sections']:
		return True
	
	return False

def raw_section_has_identifier(life, section, identifier):
	if identifier in life['raw']['sections'][section]:
		return True
	
	return False

def get_raw_sections(life):
	return life['raw']['sections'].keys()

def get_raw_identifiers(life, section):
	return life['raw']['sections'][section].keys()

def get_arguments(life, section, identifier):
	return life['raw']['sections'][section][identifier]

def translate(function):
	if not function in FUNCTION_MAP:
		raise Exception('\'%s\' is not a valid raw script function.' % function)
	
	return FUNCTION_MAP[function]
