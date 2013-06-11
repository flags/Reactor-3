from globals import *
import life as lfe

import judgement
import movement
import dialog
import speech
import raids
import brain
import camps
import jobs

import logging
import random

ENTRY_SCORE = 0

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#Note: We don't want to change the state because we're running this module alongside
	#other modules that will (most likely) be changing states for us...
	#Instead we're going to read the current state and react accordingly via flipping
	#life['flags'] and spawning conversations based on that (and the state of course).
	#The main focus is to provide effective output rather than a lot of it, so the less
	#conversations we spawn the better.
	
	return RETURN_SKIP

def start_dialog(life, target, gist):
	_dialog = {'type': 'dialog',
		'from': life,
		'enabled': True,
		'gist': gist}
	_dialog = dialog.create_dialog_with(life, target, _dialog)
	
	if _dialog:
		life['dialogs'].append(_dialog)
		return True
	
	return False	

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#TODO: Add these two values to an array called PANIC_STATES
	#if not alife_seen:
	#	return False
	if not 'CAN_TALK' in life['life_flags']:
		return False	
	
	for ai in alife_seen:
		#What's our relationship with them?
		#if ai['life']['state'] in ['hiding', 'hidden']:
		#	break
		
		if life['state'] in ['combat']:
			break
		
		if jobs.alife_is_factor_of_any_job(ai['life']):
			break
		
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
		
		if not 'player' in target and not lfe.get_memory(life, matches={'text': 'met', 'target': target['id']}):
			start_dialog(life, target['id'], 'introduction')
		elif lfe.get_questions(life, target=target['id']):
			if _potential_talking_targets:
				start_dialog(life, target['id'], 'questions')
	
	if life['dialogs']:
		_dialog = life['dialogs'][0]
		dialog.tick(life, _dialog)
	
	if not judgement.is_safe(life) and life['known_camps'] and camps.get_distance_to_nearest_known_camp(life)<30:
		_combat_targets = brain.retrieve_from_memory(life, 'combat_targets')
		
		if _combat_targets:
			_nearest_camp = camps.get_nearest_known_camp(life)
			_raiders = [t['who']['life']['id'] for t in _combat_targets]
			raids.create_raid(_nearest_camp['id'], join=life['id'])
			raids.add_raiders(_nearest_camp['id'], _raiders)
			
			#TODO: Remove memory call
			speech.announce(life,
				'camp_raid',
				camp=_nearest_camp,
				raiders=_raiders)

	_visible_items = [life['know_items'][item] for item in life['know_items'] if not life['know_items'][item]['last_seen_time'] and not 'id' in life['know_items'][item]['item']]
	for ai in [life['know'][i] for i in life['know']]:
		if judgement.is_target_dangerous(life, ai['life']['id']):
			continue
		
		if life['state'] == 'combat':
			break
		
		if ai['life']['state'] in ['hiding', 'hidden']:
			break

		for item in _visible_items:
			#TODO: Check
			if brain.has_shared_item_with(life, ai['life'], item['item']):
				continue

			#_item_chunk_key = '%s,%s' % ((item['item']['pos'][0]/SETTINGS['chunk size'])*SETTINGS['chunk size'],
			#	(item['item']['pos'][1]/SETTINGS['chunk size'])*SETTINGS['chunk size'])

			if not item['item']['uid'] in ITEMS:
				continue

			brain.share_item_with(life, ai['life'], item['item'])
			speech.communicate(life,
				'share_item_info',
				item=brain.get_remembered_item(life, item['item']),
				matches=[{'id': ai['life']['id']}])
			#speech.communicate(life,
				#'share_chunk_info',
				#chunk_key=_item_chunk_key,
				#matches=[{'id': ai['life']['id']}])
			#speech.send(life, ai['life'], 'share_chunk_info')e
		
		#_nearest_camp = camps.get_nearest_known_camp(life)
		
		#if _nearest_camp and camps.is_in_camp(life, _nearest_camp):
			#if not speech.has_sent(life, ai['life'], 'welcome_to_camp') and _nearest_camp['founder'] == life['id']:
				#if WORLD_INFO['ticks']-_nearest_camp['time_discovered']<=1000:
					#msg = 'Welcome to camp, new guy!'
				#else:
					#msg = 'Welcome back to camp.'

				#speech.communicate(life,
						#'welcome_to_camp',
						#msg=msg,
						#matches=[{'id': ai['life']['id']}])
				#speech.send(life, ai['life'], 'welcome_to_camp')

	#_all_targets = targets_seen
	#_all_targets.extend(targets_not_seen)
	#for ai in _all_targets:
		#speech.announce(life, 'under_attack', attacker=ai['who']['life'])
