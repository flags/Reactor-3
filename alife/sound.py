from globals import *

import graphics as gfx
import life as lfe

import judgement
import dialog
import action
import groups
import chunks
import speech
import combat
import events
import raids
import brain
import camps
import stats
import maps
import jobs

import logging

def listen(life):
	for event in life['heard'][:]:
		if not event['from']['id'] in life['know']:
			pass
			#logging.warning('%s does not know %s!' % (' '.join(event['from']['name']),' '.join(life['name'])))
		
		#if event_delay(event, 20):
		#	return False
		
		if not brain.knows_alife(life, event['from']):
			brain.meet_alife(life, event['from'])
			
			logging.info('%s learned about %s via listen.' % (' '.join(life['name']), ' '.join(event['from']['name'])))
		
		if event['gist'] == 'follow':
			if stats.will_obey(life, event['from']['id']):
				brain.add_impression(life, event['from']['id'], 'follow', {'influence': stats.get_influence_from(life, event['from']['id'])})
		
		elif event['gist'] == 'surrender':
			_found_related_job = False
			
			if not life['task']:
				for _j in jobs.find_jobs_of_type('surrender'):
					if jobs.alife_is_factor_of_job(event['from'], _j):
						_found_related_job = True
						break
					
					if jobs.is_working_job(life, _j):
						_found_related_job = True
						break
					
					if jobs.is_job_candidate(_j, life):
						_found_related_job = True
						break
			else:
				_found_related_job = True
			
			#DEBUG
			_found_related_job = True
			
			if not _found_related_job:
				_j = jobs.create_job(life, 'surrender')
				jobs.add_job_completed_callback(_j, combat.disarm_completed)
				jobs.add_leave_job_callback(_j, combat.disarm_left)
				jobs.add_job_factor(_j, 'alife', event['from'])
				jobs.add_job_task(_j, 'disarm', callback=combat.disarm, required=True)
				jobs.add_job_task(_j, 'guard', callback=combat.guard, depends_on='disarm')
				jobs.add_job_task(_j, 'fetch_item', callback=combat.retrieve_weapon, depends_on='guard')
				jobs.add_job_task(_j, 'guard', callback=combat.guard)
				jobs.add_job_candidate(_j, life)
				jobs.announce_job(life, _j)
				jobs.process_job(_j)
		
		elif event['gist'] == 'target_surrendered':
			if not brain.knows_alife(life, event['target']):
				brain.meet_alife(life, event['target'])
			
			print life['name'],'Got secondhand knowledge of a surrender'
		
		elif event['gist'] == 'demand_drop_item':
			if event_delay(event, 120):
				continue
			
			_inventory_item = lfe.get_inventory_item(life,event['item'])
			
			brain.flag_item(life, _inventory_item,'demand_drop')
			lfe.say(life,'@n begins to drop their %s.' % _inventory_item['name'],action=True)
			
			speech.communicate(life, 'dropped_demanded_item', matches=[{'id': event['from']['id']}])
			
			lfe.add_action(life,{'action': 'dropitem',
				'item': event['item']},
				401,
				delay=20)
		
		elif event['gist'] == 'move_away_from_item':
			#'/'''/s'/sc'/sc/sc/'/'ssc/''/'ssc/'sc/'sc/'sc/'sac/'asc/'cas/''s/as/'s/'aasc/'
			pass
		
		elif event['gist'] == 'looks_hostile':
			#speech.communicate(life, 'surrender', matches=[{'id': event['from']['id']}])
			pass
		
		elif event['gist'] == 'camp_raid':
			print '*' * 10
			print 'RAID IN EFFECT!!!!!!!!!!'
			print '*' * 10
			_knows = brain.knows_alife(life, event['from'])
			_raid = raids.defend_camp(event['camp']['id'], life['id'])
			
			if _knows and not judgement.is_target_dangerous(life, _knows['life']['id']):
				lfe.memory(life, 'heard about a camp raid', camp=event['camp']['id'])
				_raid_score = judgement.judge_raid(life, event['raiders'], event['camp']['id'])
				speech.announce(life, 'raid_score', raid_score=_raid_score)
		
		elif event['gist'] == 'raid_score':
			print life['name'],'Got friendly raid score:', event['raid_score'] 
		
		elif event['gist'] == 'greeting':
			if event['from']['camp'] and not camps.has_discovered_camp(life, event['from']['camp']):
				camps.discover_camp(life, event['from']['known_camps'][event['from']['camp']])
			
			if not speech.has_sent(life, event['from'], 'greeting'):
				speech.send(life, event['from'], 'friendly')
			
			if not speech.has_received(life, event['from'], 'greeting'):
				speech.receive(life, event['from'], 'greeting')
		
		elif event['gist'] == 'ask_about_recent_events':
			_event = speech.determine_interesting_event(life, event['from'])
			
			if _event:
				lfe.say(life, _event)
		
		elif event['gist'] == 'get_chunk_info':
			if event_delay(event, 60):
				continue

			if speech.has_sent(life, event['from'], 'get_chunk_info'):
				continue

			if not speech.has_received(life, event['from'], 'get_chunk_info'):
				speech.communicate(life, 'get_chunk_info', target=event['from'])
				speech.receive(life, event['from'], 'get_chunk_info')
				speech.send(life, event['from'], 'no_chunk_info')
				lfe.say(life, 'I\'m new around here, sorry!')
		
		elif event['gist'] == 'share_chunk_info':
			if 'chunk_key' in event:
				maps.refresh_chunk(event['chunk_key'])
				judgement.judge_chunk(life, event['chunk_key'])
				lfe.memory(life, 'heard about a chunk', target=event['from']['id'])

		elif event['gist'] == 'share_item_info':
			if not brain.has_remembered_item(life, event['item']['item']):
				lfe.memory(life, 'heard about an item',
					item=event['item']['item'],
					target=event['from']['id'])
				brain.remember_item_secondhand(life, event['from'], event['item'])
		
		elif event['gist'] == 'share_camp_info':
			if event_delay(event, 30):
				#TODO: This is only a PoC. The ALife stops to interpret the information.
				lfe.clear_actions(life)
				continue
			
			if not camps.has_discovered_camp(life, event['camp']['id']):
				camps.discover_camp(life, event['camp'])
				
				#TODO: Judge and respond?
				lfe.memory(life, 'heard about camp',
					camp=event['camp']['id'],
					target=event['from']['id'],
					founder=event['founder'])
		
		elif event['gist'] == 'welcome_to_camp':
			if event_delay(event, 20):
				continue
			
			if not speech.has_received(life, event['from'], 'welcome_to_camp'):
				lfe.say(life, 'It\'s good to be here.')
				speech.receive(life, event['from'], 'welcome_to_camp')
		
		elif event['gist'] == 'who_is_founder':
			#TODO: Who do we believe is the founder?
			_helped = False
			
			if event['camp'] in [camp['id'] for camp in camps.get_founded_camps(life)]:
				speech.communicate(life,
					'camp_founder',
					founder=life['id'],
					camp=event['camp'],
					matches=[{'id': event['from']['id']}])
				_helped = True
			
			else:
				for founder in lfe.get_memory(life, matches={'camp': event['camp'], 'text': 'heard about camp', 'founder': '*'}):
					speech.communicate(life,
						'camp_founder',
						founder=founder['target'],
						camp=event['camp'],
						matches=[{'id': event['from']['id']}])
					_helped = True
					break
			
			if not _helped:
				lfe.memory(life, 'help find founder',
					camp=event['camp'],
					target=event['from']['id'])
				speech.communicate(life,
					'dont_know_founder',
					camp=event['camp'],
					matches=[{'id': event['from']['id']}])
		
		elif event['gist'] == 'dont_know_founder':
			lfe.memory(life, 'dont know founder',
				camp=event['camp'],
				target=event['from']['id'])
		
		elif event['gist'] == 'camp_founder':
			lfe.memory(life, 'heard about camp',
				camp=event['camp'],
				target=event['founder'],
				founder=event['founder'])
			
			print 'Thanks for the camp founder info!'
		
		elif event['gist'] == 'appear_friendly':
			#if not lfe.get_memory(life, matches={'target': event['from']['id'], 'text': 'hostile'}):
			lfe.memory(life, 'friendly',
				target=event['from']['id'])
		
		elif event['gist'] == 'appear_hostile':
			#if not lfe.get_memory(life, matches={'target': event['from']['id'], 'text': 'friendly'}):
			lfe.memory(life, 'hostile',
				target=event['from']['id'])
		
		elif event['gist'] == 'under_attack':
			_knows_attacker = True
			
			if life['id'] == event['attacker']:
				pass
			else:
				if not brain.knows_alife_by_id(life, event['attacker']):
					brain.meet_alife(life, LIFE[event['attacker']])
					_knows_attacker = False
				
				_target = brain.knows_alife_by_id(life, event['attacker'])
				_believes = judgement.believe_which_alife(life, [event['from']['id'], event['attacker']])
	
				#SITUATION 1: We believe it
				if _believes == event['from']['id']:
					lfe.memory(life, 'heard about attack',
						attacker=event['attacker'],
						target=event['from']['id'])
					#lfe.memory(life, 'target attacked victim',
					#	target=event['attacker'],
					#	victim=event['from']['id'],
					#	trust=-brain.knows_alife_by_id(life, event['from']['id'])['trust'],
					#	danger=5)
					
					if event['last_seen_at']:
						_target['last_seen_at'] = event['last_seen_at'][:]
					else:
						_target['last_seen_at'] = event['from']['pos'][:]
				else:
					lfe.memory(life, 'reject under_attack: attacker is trusted',
						attacker=event['attacker'],
						target=event['from']['id'])
						
					lfe.create_question(life,
						'opinion_of_target',
						{'target': event['from']['id'], 'who': event['attacker']},
						[{'text': 'target trusts target', 'target': event['from']['id'], 'who': event['attacker']},
					     {'text': 'target doesn\'t trust target', 'target': event['from']['id'], 'who': event['attacker']},
					     {'text': 'target doesn\'t know target', 'target': event['from']['id'], 'who': event['attacker']}],
						answer_all=True,
						interest=10)
			
			#if _believes == event['from']['id']:
			#	if lfe.get_memory(life, matches={'target': event['attacker']['id'], 'text': 'friendly'}):
			#		lfe.memory(life, 'traitor',
			#			target=event['attacker']['id'])
			#		lfe.say(life, 'You no-good traitor!')
			#
			#	lfe.memory(life, 'hostile',
			#		target=event['attacker']['id'])
			#else:
			#	if lfe.get_memory(life, matches={'target': event['from']['id'], 'text': 'friendly'}):
			#		lfe.memory(life, 'traitor',
			#			target=event['from']['id'])
			#		lfe.say(life, 'You no-good traitor!')
			#	
			#	lfe.memory(life, 'hostile',
			#		target=event['from']['id'])
			#
			#TODO: Radio back and ask where the target is (randomly have the sending ALife leave this info out so we have to ask)
			#if not 'location' in event and not speech.has_sent(life, event['from'], 'get_alife_location'):
			#	speech.communicate(life,
			#		'get_alife_location',
			#		alife=event['attacker'],
			#		matches=[{'id': event['from']['id']}])
			#	lfe.say(life, 'Where is he?')
			#elif 'location' in event:
			#	_target['last_seen_at'] = event['attacker']['pos'][:]
		
		elif event['gist'] == 'get_alife_location':
			_target = brain.knows_alife(life, event['alife'])
			
			speech.communicate(life,
				'alife_location',
				alife=event['alife'],
				location=_target['last_seen_at'][:],
				matches=[{'id': event['from']['id']}])
		
		elif event['gist'] == 'alife_location':
			_target = brain.knows_alife(life, event['alife'])
			
			#TODO: Trust should play a factor here (and also when we ask for the location too)
			_target['last_seen_at'] = event['location']
		
		elif event['gist'] == 'consume_item':
			lfe.memory(life, 'consume_item', target=event['from']['id'])
		
		elif event['gist'] == 'target_needs_disarmed':
			if not brain.knows_alife(life, event['alife']):
				brain.meet_alife(life, event['alife'])
			
			#TODO: In the future we should consider giving this task to another ALife
			#_target = brain.knows_alife(life, event['alife'])['score']
			logging.warning('target_needs_disarmed: Needs handling code.')
		
		elif event['gist'] == 'group_set_shelter':
			if 'player' in life:
				gfx.radio(event['from'], 'Camp established at marker %s.' % ','.join(event['chunk_id']))
			else:
				judgement.judge_chunk(life, event['chunk_id'])
				
				print 'GOT SHELTER INFO' * 100
			
			events.accept(groups.get_event(life['group'], event['event_id']), life['id'])
		
		elif event['gist'] == 'group_location':
			if groups.is_leader(event['group_id'], life['id']):
				_shelter = groups.get_shelter(event['group_id'])
				
				if _shelter:
					speech.communicate(life,
						               'answer_group_location',
						               matches=[{'id': event['from']['id']}],
						               group_id=event['group_id'],
						               location=_shelter)
				else:
					speech.communicate(life,
						               'answer_group_location_fail',
						               matches=[{'id': event['from']['id']}],
						               group_id=event['group_id'])
		
		elif event['gist'] == 'answer_group_location':
			gfx.radio(event['from'], 'We\'re at marker %s.' % ','.join(event['location']))
		
		elif event['gist'] == 'answer_group_location_fail':
			gfx.radio(event['from'], 'We don\'t have a camp yet. I\'ll let you know when we meet up.')
		
		elif event['gist'] == 'group_jobs':
			if groups.is_leader(event['group_id'], life['id']):
				_jobs = groups.get_jobs(event['group_id'])
				
				if _jobs:
					gfx.radio(life, 'I\'ve got a few jobs for you...')
					speech.start_dialog(event['from'], life['id'], 'jobs')
		
		elif event['gist'] == 'job':
			groups.discover_group(life, event['from']['group'])
			
			if judgement.can_trust(life, event['from']['id']):
				jobs.join_job(event['job_id'], life['id'])
		
		else:
			logging.warning('Unhandled ALife context: %s' % event['gist'])
		
		life['heard'].remove(event)

def event_delay(event,time):
	if event['age'] < time:
		event['age'] += 1
		
		return True
	
	return False
