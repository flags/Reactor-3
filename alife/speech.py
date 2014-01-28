from globals import *

import graphics as gfx
import life as lfe

import judgement
import language
import dialog
import groups
import memory
import brain
import menus
import sight
import stats

import logging
import random

def has_sent(life, target_id, gist):
	if gist in life['know'][target_id]['sent']:
		return life['know'][target_id]['sent'][gist]
	
	return False

def send(life, target_id, gist):
	life['know'][target_id]['sent'][gist] = WORLD_INFO['ticks']
		
	return True

def announce(life, gist, public=False, trusted=False, group=None, filter_if=None, **kwargs):
	"""Sends `gist` to any known ALife. If `public`, then send to everyone."""
	if public:
		_announce_to = [LIFE[i] for i in LIFE if not i == life['id']]
	elif trusted:
		_announce_to = [life['know'][i]['life'] for i in life['know'] if life['know'][i]['alignment'] == 'trust']
	elif group:
		_announce_to = [LIFE[i] for i in groups.get_group(life, group)['members'] if not i == life['id']]
	else:
		_announce_to = [life['know'][i]['life'] for i in life['know'] if not judgement.is_target_dangerous(life, i)]
	
	for target in _announce_to:
		if not stats.can_talk_to(life, target['id']):
			continue
		
		if filter_if and filter_if(target['id']):
			continue
		
		_radio = False
		if not sight.can_see_position(life, target['pos']):
			if lfe.get_all_inventory_items(life, matches=[{'name': 'radio'}]):
				_radio = True
			else:
				continue
	
		memory.create_question(life, target['id'], gist, **kwargs)
	
	return True

def get_announce_list(life):
	return [life['know'][i]['life'] for i in life['know'] if life['know'][i]['score']>0]

def communicate(life, gist, msg=None, radio=False, matches=[], **kvargs):
	if 'target' in kvargs:
		logging.warning('Deprecated keyword in speech.communicate(): target')
	
	lfe.create_conversation(life, gist, msg=msg, radio=radio, matches=matches, **kvargs)
	lfe.create_and_update_self_snapshot(life)

def start_dialog(life, _target_id, gist, remote=False, **kwargs):
	_dialog = dialog.create_dialog_with(life, _target_id, remote=remote, **kwargs)
	
	#if 'ignore_if_said_in_last' in kwargs:
	#	if kwargs['ignore_if_said_in_last'] == -1 and has_sent(life, target_id, gist):
	#		return False
	#	elif WORLD_INFO['ticks']-has_sent(life, target_id, gist)<kwargs['ignore_if_said_in_last']:
	#		return False
	#	
	#	send(life, target_id, gist)
	
	dialog.say_via_gist(life, _dialog, gist)

def determine_interesting_event(life, target):
	_valid_phrases = []
	for memory in life['memory']:
		_memory_age = WORLD_INFO['ticks']-memory['time_created']
		
		if _memory_age >= 500:
			continue
		
		if memory['target'] == target['id']:
			continue
		
		_phrase = language.generate_memory_phrase(memory)
		
		if not _phrase:
			continue
		
		_valid_phrases.append(_phrase)
	
	if not _valid_phrases:
		return 'I don\'t have anything interesting to say.'
		
	return random.choice(_valid_phrases)

def get_recent_events(life):
	if WORLD_INFO['ticks']-life['created']<75:
		return 'Hey, I just got here!'
	
	return 'Nothing much has been going on lately.'

def get_target(life, dialog_id, gist):
	if 'player' in life:
		_targets = menus.create_target_list()
		
		_menu = menus.create_menu(menu=_targets,
		                          title='Select Target',
		                          format_str='$k',
		                          on_select=confirm_target,
		                          close_on_select=True)
		menus.activate_menu(_menu)
	else:
		dialog.get_dialog(dialog_id)['flags']['target'] = random.choice(judgement.get_threats(life))
		dialog.say_via_gist(life,
			                dialog_id,
			                dialog.get_flag(dialog_id, 'NEXT_GIST'))

def get_needs(life, dialog_id, gist):
	if 'player' in life:
		_items = []
		
		for item_type in ITEM_TYPES:
			_items.append(menus.create_item('list',
			                                item_type.title(),
			                                ['Skip', 'Need'],
			                                icon=ITEM_TYPES[item_type]['icon'],
			                                item_name=item_type))
		
		_menu = menus.create_menu(menu=_items,
		                          title='Select Items',
		                          format_str='[$i] $k: $v',
		                          padding=[1, 1],
		                          on_select=lambda entry: confirm_items(dialog_id, _items),
		                          close_on_select=True)
		menus.activate_menu(_menu)
	else:
		raise Exception('Dead end.')

def get_introduction_message(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	
	if _target['alignment'] == 'hostile':
		return ['Enemy spotted!']
	
	_alignment = stats.get_goal_alignment_for_target(life, life_id)
	
	if _alignment == 'feign_trust':
		return 'Let\'s have a chat.'
	
	if _alignment == 'hostile':
		return 'Die!'
	
	if _alignment == 'trust':
		return ['Hello traveler.', 'Greetings.']

def get_introduction_gist(life, life_id):
	_alignment = stats.get_goal_alignment_for_target(life, life_id)
	
	if _alignment == 'hostile':
		return 'hostile_response'
	
	if _alignment == 'feign_trust':
		return 'feign_trust_failed'
	
	return 'potential_trust'

def describe_target(life, life_id):
	if life['id'] == life_id:
		return 'That\'s me.'
	
	_target = brain.knows_alife_by_id(life, life_id)
	_details = []
	
	if _target['dead']:
		return 'He died.'
	
	if sight.can_see_target(life, life_id):
		_details.append('He\'s right over there!')
	else:
		if _target['last_seen_time'] >= 2000:
			_details.append('I last saw him at %s, %s, but it was a long time ago.' % (_target['last_seen_at'][0], _target['last_seen_at'][1]))
		else:
			_details.append('I last saw him at %s, %s, recently.' % (_target['last_seen_at'][0], _target['last_seen_at'][1]))
	
	return ' '.join(_details)

def get_group_stage_message(life):
	_group_stage = groups.get_stage(life, life['group'])
	
	if _group_stage == STAGE_SETTLING:
		return ['Keep an eye out for places to camp.', 'Look for possible camps!', 'Let\'s find a camp, guys.']
	
	return 'HE LIVES'

def get_known_group(life, life_id):
	_target = brain.knows_alife_by_id(life, life_id)
	_dialog_id = lfe.has_dialog_with(life, life_id)
	
	if 'player' in life:
		_menu_items = []
		
		for group_id in life['known_groups']:
			if _target['group'] == group_id:
				continue
			
			_menu_items.append(menus.create_item('single', group_id, None, group=group_id, dialog_id=_dialog_id))
		
		if not _menu_items:
			gfx.message('You don\'t know of any other groups.')
			return False
		
		_menu = menus.create_menu(menu=_menu_items,
		                          title='Inform of Group',
		                          format_str='$k',
		                          on_select=confirm_inform_of_group,
		                          close_on_select=True)
		menus.activate_menu(_menu)
	else:
		raise Exception('Dead end.')

def confirm_target(entry):
	_dialog_id = LIFE[SETTINGS['controlling']]['dialogs'][0]
	for flag in dialog.get_dialog(_dialog_id)['flags']:
		if dialog.get_dialog(_dialog_id)['flags'][flag] == -333:
			dialog.get_dialog(_dialog_id)['flags'][flag] = entry['target']
			break
	
	dialog.say_via_gist(LIFE[SETTINGS['controlling']],
	                    _dialog_id,
	                    dialog.get_flag(_dialog_id, 'NEXT_GIST'))

def confirm_items(dialog_id, items):
	_item_types = []
	
	for entry in items:
		if entry['values'][entry['value']] == 'Need':
			_item_types.append({'name': entry['item_name']})
	
	for flag in dialog.get_dialog(dialog_id)['flags']:
		if dialog.get_dialog(dialog_id)['flags'][flag] == -333:
			dialog.get_dialog(dialog_id)['flags'][flag] = _item_types
			break
	
	dialog.say_via_gist(LIFE[SETTINGS['controlling']],
	                    dialog_id,
	                    dialog.get_flag(dialog_id, 'NEXT_GIST'))

def confirm_inform_of_group(entry):
	_dialog_id = entry['dialog_id']
	
	if 'group' in entry:
		for flag in dialog.get_dialog(_dialog_id)['flags']:
			if dialog.get_dialog(_dialog_id)['flags'][flag] == -333:
				dialog.get_dialog(_dialog_id)['flags'][flag] = entry['group']
				break
		
		dialog.say_via_gist(LIFE[SETTINGS['controlling']],
			                _dialog_id,
			                dialog.get_flag(_dialog_id, 'NEXT_GIST'))

def confirm_inform_of_group_members(entry):
	_dialog_id = entry['dialog_id']
	_members = []
	
	for entry in entry['members']:
		if entry['values'][entry['value']] == 'Member':
			_members.append(entry['target_id'])
	
	dialog.say_via_gist(LIFE[SETTINGS['controlling']],
                        _dialog_id,
                        'group_list',
	                    group_list=_members,
	                    group_id=entry['group'])

def inform_of_items(life, life_id, item_matches):
	for item_uid in brain.get_multi_matching_remembered_items(life, item_matches):
		_remembered_item = brain.get_remembered_item(life, item_uid)
		brain.update_item_secondhand(LIFE[life_id], _remembered_item)
	
	return 'I\'ve added some locations to your PDA. Check there.'

def inform_of_group(life, life_id):
	memory.create_question(life, life_id, 'group_exists',
	                       group_id=life['group'],
	                       group_list=groups.get_group(life, life['group'])['members'])

def force_inform_of_group(life, life_id):
	groups.discover_group(LIFE[life_id], life['group'])

def inform_of_group_members(life, life_id, group_id):
	if 'player' in life:
		_dialog_id = lfe.has_dialog_with(life, life_id)
		_menu_items = []
		
		for target_id in life['know']:
			if target_id == life['id'] or target_id == life_id:
				continue
			
			if groups.is_member(life, group_id, target_id):
				_colors = (tcod.green, tcod.white)
				_values = ['Member', 'Not Member']
			else:
				_colors = (tcod.red, tcod.white)
				_values = ['Not Member', 'Member']
			
			_menu_items.append(menus.create_item('list',
			                                     ' '.join(LIFE[target_id]['name']),
			                                     _values,
			                                     group=group_id,
			                                     target_id=target_id,
			                                     members=_menu_items,
			                                     color=_colors,
			                                     dialog_id=_dialog_id))
		
		if not _menu_items:
			return False
		
		_menu = menus.create_menu(menu=_menu_items,
		                          title='Inform of Group Members',
		                          format_str='$k: $v',
		                          on_select=confirm_inform_of_group_members,
		                          close_on_select=True)
		menus.activate_menu(_menu)
	else:
		for target_id in groups.get_group(life, group_id)['members']:
			if life['id'] == target_id:
				continue
			
			memory.create_question(life, target_id, 'group_list',
				                   group_id=group_id,
				                   group_list=groups.get_group(life, group_id)['members'])

def update_group_members(life, target_id, group_id, group_list):
	_known_members = groups.get_group(life, group_id)['members'][:]
	_group_list = group_list[:]
	_send = []
	
	for member in _group_list:
		if not member in _known_members:
			_known_members.append(member)
			groups.add_member(life, group_id, member)
	
	for member in _known_members:
		if not member in group_list:
			_send.append(member)
	
	if _send:
		memory.create_question(life, target_id, 'group_list',
		                       group_id=life['group'],
		                       group_list=groups.get_group(life, life['group'])['members'])

def update_location_of_target_from_target(life, life_id, target_id):
	_known = brain.knows_alife_by_id(life, target_id)
	_target_known = brain.knows_alife_by_id(LIFE[life_id], target_id)	
	
	if _target_known['last_seen_time'] == -1:
		return False
	
	if _target_known['last_seen_time'] < _known['last_seen_time'] or not _known['last_seen_at']:
		_known['last_seen_at'] = _target_known['last_seen_at']
		_known['last_seen_time'] = _target_known['last_seen_time']
		
		logging.debug('%s updated location of %s: %s' % (' '.join(life['name']), ' '.join(LIFE[target_id]['name']), _known['last_seen_at']))
	else:
		print 'Got out of date info!' * 20

def change_alignment(life, life_id, alignment):
	_alignment = '%s_to_%s' % (brain.knows_alife_by_id(life, life_id)['alignment'], alignment)
	
	if not has_sent(life, life_id, _alignment):
		start_dialog(life, life_id, _alignment)
		send(life, life_id, _alignment)

def announce_combat_to_group(life, group_id):
	_number_of_members = len(groups.get_group(life, group_id)['members'])
	
	if _number_of_members>=5:
		groups.announce(life, group_id, 'group_prepare_for_combat_large')
	elif _number_of_members>2:
		groups.announce(life, group_id, 'group_prepare_for_combat_small')
	else:
		groups.announce(life, group_id, 'group_prepare_for_combat_partner')