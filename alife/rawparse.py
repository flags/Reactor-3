from globals import *

import life as lfe

import references
import judgement
import survival
import movement
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
		'is_compatible_with': stats.is_compatible_with,
		'can_trust': judgement.can_trust,
		'is_dangerous': judgement.is_target_dangerous,
		'can_bite': stats.can_bite,
		'can_scratch': stats.can_scratch,
		'weapon_equipped_and_ready': combat.weapon_equipped_and_ready,
		'prepare_for_ranged': combat.prepare_for_ranged,
		'explore_unknown_chunks': survival.explore_unknown_chunks,
		'is_nervous': stats.is_nervous,
		'is_aggravated': stats.is_aggravated,
		'is_safe': judgement.is_safe,
		'is_healthy': None,
		'is_intimidated': stats.is_intimidated,
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
		'is_child_of': stats.is_child_of,
		'is_parent_of': stats.is_parent_of,
		'has_parent': stats.has_parent,
		'has_child': stats.has_child,
		'is_night': logic.is_night,
		'is_born_leader': stats.is_born_leader,
		'is_safe_in_shelter': stats.is_safe_in_shelter,
		'is_incapacitated': stats.is_incapacitated,
		'is_target': lambda life, life_id: life_id in judgement.get_targets(life) or life_id in judgement.get_combat_targets(life),
		'is_combat_target': lambda life, life_id: life_id in judgement.get_combat_targets(life),
		'is_traitor': lambda life, life_id: len(lfe.get_memory(life, matches={'text': 'traitor', 'target': life_id}))>0,
		'is_awake': judgement.is_target_awake,
		'is_dead': judgement.is_target_dead,
		'find_and_announce_shelter': groups.find_and_announce_shelter,
		'desires_shelter': stats.desires_shelter,
		'travel_to_position': movement.travel_to_position,
		'find_target': movement.find_target,
		'can_see_target': sight.can_see_target,
		'has_threats': lambda life: len(judgement.get_threats(life))>0,
		'has_targets': lambda life: len(judgement.get_targets(life))>0,
		'has_visible_targets': lambda life: len(judgement.get_visible_threats(life))>0,
		'has_combat_targets': lambda life: len(judgement.get_combat_targets(life))>0,
		'has_ready_combat_targets': lambda life: len(judgement.get_ready_combat_targets(life, recent_only=True, limit_distance=sight.get_vision(life)+10))>0,
		'danger_close': stats.is_combat_target_too_close,
		'number_of_alife_in_chunk_matching': lambda life, chunk_key, matching, amount: len(chunks.get_alife_in_chunk_matching(chunk_key, matching))>amount,
		'number_of_alife_in_reference_matching': lambda life, reference_id, matching, amount: len(references.get_alife_in_reference_matching(reference_id, matching))>amount,
		'announce_to_group': groups.announce,
		'is_in_chunk': chunks.is_in_chunk,
		'has_completed_job': lambda life, job_id: job_id in life['completed_jobs'],
		'has_completed_task': lambda life, job_id: job_id in life['completed_jobs'],
		'retrieve_from_memory': brain.retrieve_from_memory,
		'pick_up_and_hold_item': lfe.pick_up_and_hold_item,
		'has_usable_weapon': combat.has_potentially_usable_weapon,
		'target_is_combat_ready': judgement.target_is_combat_ready,
		'get_group': lambda life: life['group'],
		'join_group': lambda life, life_id: groups.add_member(LIFE[life_id]['group'], life['id']),
		'is_group_leader': lambda life: groups.is_leader_of_any_group(life)==True,
		'is_in_same_group': lambda life, life_id: (life['group'] and LIFE[life_id]['group'] == life['group'])>0,
		'is_target_group_leader': lambda life, life_id: (groups.is_leader_of_any_group(LIFE[life_id]))==True,
		'is_target_group_friendly': stats.is_target_group_friendly,
		'get_group_flag': groups.get_flag,
		'get_flag': brain.get_flag,
		'create_item_need': survival.add_needed_item,
		'group_needs_resources': lambda life, group_id: groups.needs_resources(group_id),
		'has_needs_to_meet': survival.has_needs_to_meet,
		'has_unmet_needs': survival.has_unmet_needs,
		'has_needs_to_satisfy': survival.has_needs_to_satisfy,
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
	     'get_location': lambda life: '%s, %s' % (life['pos'][0], life['pos'][1]),
		'has_questions_for_target': lambda life, life_id: len(memory.get_questions_for_target(life, life_id))>0,
		'ask_target_question': memory.ask_target_question,
		'consume': lfe.consume,
		'explode': items.explode,
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

def translate(function):
	if not function in FUNCTION_MAP:
		raise Exception('\'%s\' is not a valid raw script function.' % function)
	
	return FUNCTION_MAP[function]
