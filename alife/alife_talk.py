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

ENTRY_SCORE = 0
TIER = TIER_PASSIVE

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#Note: We don't want to change the state because we're running this module alongside
	#other modules that will (most likely) be changing states for us...
	#Instead we're going to read the current state and react accordingly via flipping
	#life['flags'] and spawning conversations based on that (and the state of course).
	#The main focus is to provide effective output rather than a lot of it, so the less
	#conversations we spawn the better.
	
	return RETURN_SKIP

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#TODO: Add these two values to an array called PANIC_STATES
	#if not alife_seen:
	#	return False
	
	if brain.retrieve_from_memory(life, 'tension_spike') >= 10:
		lfe.say(life, '@n panics!', action=True)
	
	_potential_talking_targets = []
	if not life['state'] in ['combat', 'hiding', 'hidden']:
		for ai in alife_seen:
			if not stats.can_talk_to(life, ai['life']['id']):
				continue
			
			if stats.has_attacked_self(life, ai['life']['id']):
				stats.react_to_attack(life, ai['life']['id'])
			elif judgement.is_target_dangerous(life, ai['life']['id']):
				if not speech.discussed(life, ai['life'], 'looks_hostile'):
					speech.communicate(life, 'looks_hostile', msg='...', matches=[{'id': ai['life']['id']}])
					speech.send(life, ai['life'], 'looks_hostile')
		
			else:
				if not stats.desires_first_contact_with and not stats.desires_conversation_with(life, ai['life']['id']):
					continue
		
				#TODO: Not always true.
				if ai['life']['state'] in ['hiding', 'hidden']:
					continue
		
				_potential_talking_targets.append(ai['life'])
	
	#TODO: Score these
	random.shuffle(_potential_talking_targets)
	
	for target in _potential_talking_targets:
		if life['dialogs']:
			print 'existing'
			break
		
		if stats.desires_first_contact_with(life, target['id']):
			speech.start_dialog(life, target['id'], 'establish_relationship')
			# and stats.desires_interaction(life):
			#if stats.desires_life(life, target['id']):
			#	speech.start_dialog(life, target['id'], 'introduction')
			#elif not stats.desires_life(life, target['id']) and not brain.get_alife_flag(life, target['id'], 'not_friend'):
			#	speech.start_dialog(life, target['id'], 'introduction_negative')
			#	brain.flag_alife(life, target['id'], 'not_friend')
		if memory.get_questions_for_target(life, target['id']):
			speech.start_dialog(life, target['id'], memory.ask_target_question(life, target['id']))
		elif memory.get_orders_for_target(life, target['id']):
			speech.start_dialog(life, target['id'], 'give_order')
		elif stats.wants_group_member(life, target['id']):
			memory.create_question(life, target['id'], 'recruit')
	
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

			speech.announce(life, 'under_attack', trusted=True, attacker=target, last_seen_at=_last_seen_at)

	_visible_items = [life['know_items'][item] for item in life['know_items'] if not life['know_items'][item]['last_seen_time'] and not 'parent_id' in ITEMS[life['know_items'][item]['item']]]
	for ai in [life['know'][i] for i in life['know']]:
		if judgement.is_target_dangerous(life, ai['life']['id']):
			continue
		
		if life['state'] == 'combat':
			break
		
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
				matches=[{'id': ai['life']['id']}])