from globals import *
import life as lfe

import judgement
import movement
import dialog
import speech
import groups
import memory
import stats
import raids
import brain
import camps
import jobs

import logging
import random


def setup(life):
	#TODO: Add these two values to an array called PANIC_STATES
	#if not alife_seen:
	#	return False
	#if brain.retrieve_from_memory(life, 'tension_spike') >= 10:
	#	lfe.say(life, '@n panics!', action=True)
	
	_potential_talking_targets = []
	for ai in life['seen']:
		if not stats.can_talk_to(life, ai):
			continue
		
		if stats.has_attacked_self(life, ai):
			stats.react_to_attack(life, ai)
		elif judgement.get_tension_with(life, ai)<=.7:
			stats.react_to_tension(life, ai)
		else:
			if not stats.desires_first_contact_with(life, ai) and not stats.desires_conversation_with(life, ai):
				continue
	
			_potential_talking_targets.append(ai)
	
	if not _potential_talking_targets:
		if life['dialogs']:
			_dialog = life['dialogs'][0]
			dialog.process(life, _dialog)
		
		if not lfe.ticker(life, 'talk', 6):
			return False
	
	if lfe.get_all_inventory_items(life, matches=[{'type': 'radio'}]):
		for ai in life['know']:
			if ai in _potential_talking_targets:
				continue
			
			if not stats.can_talk_to(life, ai):
				continue
			
			_potential_talking_targets.append(ai)
	
	#TODO: Score these
	random.shuffle(_potential_talking_targets)
	
	for target in _potential_talking_targets:
		if life['dialogs']:
			break
		
		if stats.desires_first_contact_with(life, target):
			memory.create_question(life, target, 'establish_relationship', ignore_if_said_in_last=-1)
		
		if memory.get_questions_for_target(life, target):
			_question = memory.ask_target_question(life, target)
			speech.start_dialog(life, target, _question['gist'], **_question['args'])
		elif memory.get_orders_for_target(life, target):
			speech.start_dialog(life, target, 'give_order')
		elif stats.wants_group_member(life, target):
			memory.create_question(life, target, 'recruit', ignore_if_said_in_last=-1, group_id=life['group'])
	
	if life['dialogs']:
		_dialog = life['dialogs'][0]
		dialog.process(life, _dialog)	
	
	if not judgement.is_safe(life) and lfe.ticker(life, 'call_for_help', 90, fire=True):
		_combat_targets = judgement.get_ready_combat_targets(life)
		
		if _combat_targets:
			if life['camp'] and camps.is_in_camp(life, lfe.get_current_camp(life)):
				_nearest_camp = camps.get_nearest_known_camp(life)
				raids.create_raid(_nearest_camp['id'], join=life['id'])
				raids.add_raiders(_nearest_camp['id'], _combat_targets)
				
				#TODO: Remove memory call
				speech.announce(life,
					'camp_raid',
					camp=_nearest_camp,
					raiders=_combat_targets)
			
			if life['group']:
				for target in _combat_targets:
					_last_seen_at = None
					_know = brain.knows_alife_by_id(life, target)
					
					if _know:
						_last_seen_at = _know['last_seen_at']
						
					groups.distribute(life, 'under_attack', attacker=target, last_seen_at=_last_seen_at)
		
		for target in judgement.get_ready_combat_targets(life):
			_last_seen_at = None
			_know = brain.knows_alife_by_id(life, target)
			
			if _know:
				_last_seen_at = _know['last_seen_at']

			speech.announce(life, 'attacked_by_hostile', trusted=True, target_id=target, last_seen_at=_last_seen_at)

	_visible_items = [life['know_items'][item] for item in life['know_items'] if not life['know_items'][item]['last_seen_time'] and not 'parent_id' in ITEMS[life['know_items'][item]['item']]]
	for ai in [life['know'][i] for i in life['know']]:
		if judgement.is_target_dangerous(life, ai['life']['id']):
			continue
		
		#if life['state'] == 'combat':
		#	break
		
		if ai['life']['state'] in ['hiding', 'hidden']:
			break
		
		if not stats.can_talk_to(life, ai['life']['id']):
			continue

		for item in _visible_items:
			#TODO: Check
			if brain.has_shared_item_with(life, ai['life'], item['item']):
				continue

			if not item['item'] in ITEMS:
				continue

			brain.share_item_with(life, ai['life'], item['item'])
			speech.communicate(life,
				'share_item_info',
				item=item['item'],
				matches=[ai['life']['id']])