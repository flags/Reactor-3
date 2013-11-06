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
import logic
import sight
import raids
import brain
import camps
import stats
import maps
import jobs

import logging

def can_hear(life, target_id):
	#TODO: Walls, etc
	return sight.can_see_target(life, target_id)

def listen(life):
	for event in life['heard'][:]:
		if not event['from']['id'] in life['know']:
			pass
		
		if not brain.knows_alife(life, event['from']):
			brain.meet_alife(life, event['from'])
			
			logging.info('%s learned about %s via listen.' % (' '.join(life['name']), ' '.join(event['from']['name'])))
		
		if event['gist'] == 'looks_hostile':
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

		elif event['gist'] == 'share_item_info':
			if event['item'] in ITEMS:
				if not brain.has_remembered_item(life, event['item']):
					lfe.memory(life, 'heard about an item',
						item=event['item'],
						target=event['from']['id'])
					brain.remember_item(life, ITEMS[event['item']])
		
		elif event['gist'] == 'camp_founder':
			lfe.memory(life, 'heard about camp',
				camp=event['camp'],
				target=event['founder'],
				founder=event['founder'])
			
			print 'Thanks for the camp founder info!'
		
		elif event['gist'] == 'under_attack':
			_knows_attacker = True
			
			if life['id'] == event['attacker']:
				pass
			else:
				print life['name'], 'HEARD CALL FOR HELP FROM', event['from']['name']
				if not brain.knows_alife_by_id(life, event['attacker']):
					brain.meet_alife(life, LIFE[event['attacker']])
					_knows_attacker = False
				
				_target = brain.knows_alife_by_id(life, event['attacker'])
				_believes = judgement.believe_which_alife(life, [event['from']['id'], event['attacker']])
	
				#SITUATION 1: We believe it
				if _believes == event['from']['id']:
					print 'OK'
					lfe.memory(life, 'heard about attack',
						attacker=event['attacker'],
						target=event['from']['id'])
					lfe.memory(life, 'target attacked victim',
						target=event['attacker'],
						victim=event['from']['id'],
						trust=-15,
						danger=5)
					
					if event['last_seen_at']:
						_target['last_seen_at'] = event['last_seen_at'][:]
					else:
						_target['last_seen_at'] = event['from']['pos'][:]
					
					judgement.judge_life(life, event['attacker'])
				else:
					print 'NO'
					lfe.memory(life, 'reject under_attack: attacker is trusted',
						attacker=event['attacker'],
						target=event['from']['id'],
					    trust=-10,
					    danger=10)
		
		elif event['gist'] == 'bit':
			#React to attack... this needs to be a function in stats.py
			if event['target'] == life['id']:
				pass
			else:
				_trust_sender = judgement.can_trust(life, event['from']['id'])
				
				if brain.knows_alife_by_id(life, event['target']):
					_trust_target = judgement.can_trust(life, event['target'], low=5)
				else:
					brain.meet_alife(life, LIFE[event['target']])
					_trust_target = False
				
				if _trust_target and not _trust_sender and 1==4:
					lfe.memory(life, 'trusted target attacked by',
					           victim=event['target'],
					           target=event['from']['id'],
					           trust=-5,
					           danger=3)

		elif event['gist'] == 'consume_item':
			lfe.memory(life, 'consume_item', target=event['from']['id'])
		
		elif event['gist'] == 'group_set_shelter':
			if 'player' in life:
				gfx.radio(event['from'], 'Camp established at marker %s.' % ','.join(event['reference_id']))
			else:
				judgement.judge_reference(life, event['reference_id'])
			
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
			
			if not jobs.is_candidate(event['job_id'], life['id']) and judgement.can_trust(life, event['from']['id']):
				jobs.add_job_candidate(event['job_id'], life['id'])
		
		elif event['gist'] == 'call':
			if judgement.can_trust(life, event['from']['id']):
				speech.start_dialog(life, event['from']['id'], 'call_accepted')
		
		elif event['gist'] == 'order_attack':
			lfe.memory(life, 'ordered to attack',
			           target=event['target'],
			           trust=-5,
			           danger=3)
		
		elif event['gist'] == 'threw_an_item':
			print 'CHECK THIS HERE' * 100
			pass
		
		elif event['gist'] == '_group_leader_state_change':
			life['think_rate'] = 0
		
		elif event['gist'] == 'dialog':
			life['dialogs'].append(event['dialog_id'])
		
		else:
			logging.warning('Unhandled ALife context: %s' % event['gist'])
		
		life['heard'].remove(event)

def event_delay(event,time):
	if event['age'] < time:
		event['age'] += 1
		
		return True
	
	return False
