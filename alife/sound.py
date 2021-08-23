from globals import *

import graphics as gfx
import life as lfe

from . import judgement
import dialog
from . import action
from . import groups
from . import chunks
from . import speech
from . import combat
import events
import logic
from . import sight
from . import raids
from . import brain
from . import camps
from . import stats
import maps
from . import jobs

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
			print('*' * 10)
			print('RAID IN EFFECT!!!!!!!!!!')
			print('*' * 10)
			_knows = brain.knows_alife(life, event['from'])
			_raid = raids.defend_camp(event['camp']['id'], life['id'])
			
			if _knows and not judgement.is_target_dangerous(life, _knows['life']['id']):
				lfe.memory(life, 'heard about a camp raid', camp=event['camp']['id'])
				_raid_score = judgement.judge_raid(life, event['raiders'], event['camp']['id'])
				speech.announce(life, 'raid_score', raid_score=_raid_score)
		
		elif event['gist'] == 'raid_score':
			print(life['name'],'Got friendly raid score:', event['raid_score']) 

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
			
			print('Thanks for the camp founder info!')
		
		elif event['gist'] == 'under_attack':
			_knows_attacker = True
			
			if life['id'] == event['attacker']:
				pass
			else:
				print(life['name'], 'HEARD CALL FOR HELP FROM', event['from']['name'])
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
					lfe.memory(life, 'target attacked victim',
						target=event['attacker'],
						victim=event['from']['id'])
					
					if event['last_seen_at']:
						_target['last_seen_at'] = event['last_seen_at'][:]
					else:
						_target['last_seen_at'] = event['from']['pos'][:]
					
					judgement.judge_life(life, event['attacker'])
				else:
					lfe.memory(life, 'reject under_attack: attacker is trusted',
						attacker=event['attacker'],
						target=event['from']['id'])
		
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
					           target=event['from']['id'])

		elif event['gist'] == 'consume_item':
			lfe.memory(life, 'consume_item', target=event['from']['id'])
		
		elif event['gist'] == 'call':
			if judgement.can_trust(life, event['from']['id']):
				speech.start_dialog(life, event['from']['id'], 'call_accepted', remote=True)
		
		elif event['gist'] == 'order_attack':
			lfe.memory(life, 'ordered to attack',
			           target=event['target'])
		
		elif event['gist'] == 'threw_an_item':
			print('CHECK THIS HERE' * 100)
			pass
		
		elif event['gist'] == '_group_leader_state_change':
			life['think_rate'] = 0
		
		elif event['gist'] == 'dialog':
			if not 'player' in life and not event['dialog_id'] in life['dialogs']:
				life['dialogs'].append(event['dialog_id'])
		
		else:
			logging.warning('Unhandled ALife context: %s' % event['gist'])
		
		life['heard'].remove(event)

def event_delay(event,time):
	if event['age'] < time:
		event['age'] += 1
		
		return True
	
	return False
