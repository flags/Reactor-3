from globals import *
import life as lfe

import judgement
import movement
import dialog
import speech
import groups
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
	
	for ai in alife_seen:
		if life['state'] in ['combat']:
			break
		
		if jobs.alife_is_factor_of_any_job(ai['life']):
			break
		
		if not stats.can_talk_to(life, ai['life']['id']):
			continue
		
		if judgement.is_target_dangerous(life, ai['life']['id']):
			if not speech.discussed(life, ai['life'], 'looks_hostile'):
				speech.communicate(life, 'looks_hostile', msg='...', matches=[{'id': ai['life']['id']}])
				speech.send(life, ai['life'], 'looks_hostile')
		else:
			if not speech.discussed(life, ai['life'], 'greeting'):
				speech.communicate(life, 'greeting', matches=[{'id': ai['life']['id']}])
				speech.send(life, ai['life'], 'greeting')
	
	_potential_talking_targets = []
	for ai in alife_seen:
		if life['state'] == 'combat':
			break
		
		if judgement.is_target_dangerous(life, ai['life']['id']):
			continue
		
		if not stats.can_talk_to(life, ai['life']['id']):
			continue		
		
		if not stats.desires_conversation_with(life, ai['life']['id']):
			continue
		
		#TODO: Not always true.
		if ai['life']['state'] in ['hiding', 'hidden']:
			break
		
		_potential_talking_targets.append(ai['life'])
	
	#TODO: Score these
	random.shuffle(_potential_talking_targets)
	
	for target in _potential_talking_targets:
		if life['dialogs']:
			break
		
		if life['state'] in ['combat', 'hiding', 'hidden']:
			break
		
		if not lfe.get_memory(life, matches={'text': 'met', 'target': target['id']}) and stats.desires_interaction(life):
			if not 'player' in target and stats.desires_life(life, target['id']):
				speech.start_dialog(life, target['id'], 'introduction')
			elif not stats.desires_life(life, target['id']) and not brain.get_alife_flag(life, target['id'], 'not_friend'):
				speech.start_dialog(life, target['id'], 'introduction_negative')
				brain.flag_alife(life, target['id'], 'not_friend')
		elif lfe.get_questions(life, target=target['id']):
			if _potential_talking_targets:
				speech.start_dialog(life, target['id'], 'questions')
		elif stats.desires_to_create_group(life):
			groups.create_group(life)
		elif stats.wants_group_member(life, target['id']) and not groups.is_member(life['group'], target['id']):
			brain.flag_alife(life, target['id'], 'invited_to_group')
			speech.start_dialog(life, target['id'], 'invite_to_group')
	
	if life['dialogs']:
		_dialog = life['dialogs'][0]
		dialog.tick(life, _dialog)	
	
	if not judgement.is_safe(life):
		_combat_targets = brain.retrieve_from_memory(life, 'combat_targets')
		
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
		
		for target in judgement.get_targets(life):
			_last_seen_at = None
			_know = brain.knows_alife_by_id(life, target)
			
			if _know:
				_last_seen_at = _know['last_seen_at']

			speech.announce(life, 'under_attack', trusted=True, attacker=target, last_seen_at=_last_seen_at)

	_visible_items = [life['know_items'][item] for item in life['know_items'] if not life['know_items'][item]['last_seen_time'] and not 'id' in life['know_items'][item]['item']]
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

			if not item['item']['uid'] in ITEMS:
				continue

			brain.share_item_with(life, ai['life'], item['item'])
			speech.communicate(life,
				'share_item_info',
				item=brain.get_remembered_item(life, item['item']),
				matches=[{'id': ai['life']['id']}])