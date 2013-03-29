import life as lfe

import judgement
import speech
import brain
import camps
import maps

import logging

def listen(life):	
	for event in life['heard'][:]:
		if not event['from']['id'] in life['know']:
			pass
			#logging.warning('%s does not know %s!' % (' '.join(event['from']['name']),' '.join(life['name'])))
		
		if event_delay(event, 20):
			return False
		
		if event['gist'] == 'surrender':
			if not speech.has_answered(life, event['from'], 'surrender'):
				#if not speech.has_answered(life, event['from'], 'greeting'):
				speech.communicate(life, 'surrender', target=event['from'])
				speech.answer(life, event['from'], 'surrender')
				print 'SURRENDERED'
			#if speech.consider(life,event['from'],'surrendered'):
			#	logging.debug('%s realizes %s has surrendered.' % (' '.join(life['name']),' '.join(event['from']['name'])))
			#	
			#	speech.communicate(life,'stand_still',target=event['from'])
		
		elif event['gist'] == 'resist':
			if speech.consider(life, event['from'], 'resist'):
				logging.debug('%s realizes %s is resisting.' % (' '.join(life['name']),' '.join(event['from']['name'])))
		
		elif event['gist'] == 'free_to_go':
			lfe.create_and_update_self_snapshot(event['from'])
			speech.unconsider(life,event['from'],'surrender')
			brain.unflag(life, 'surrendered')
			brain.unflag(life, 'scared')
		
		elif event['gist'] == 'comply':
			#TODO: Judge who this is coming from...
			lfe.clear_actions(life)
			speech.communicate(life,'surrender')
			speech.consider(life, event['from'], 'surrendered_to')
			brain.flag(life, 'surrendered')
		
		elif event['gist'] == 'demand_drop_item':
			if event['age'] < 40:
				event['age'] += 1
				communicate(life,'compliant',target=event['from'])
				
				continue
			
			_inventory_item = lfe.get_inventory_item(life,event['item'])
			
			flag_item(life,_inventory_item,'demand_drop')
			lfe.say(life,'@n begins to drop their %s.' % _inventory_item['name'],action=True)
			
			lfe.add_action(life,{'action': 'dropitem',
				'item': event['item']},
				401,
				delay=20)
		
		elif event['gist'] == 'stand_still':
			if brain.get_flag(life, 'surrendered'):
				lfe.clear_actions(life)
				lfe.add_action(life,{'action': 'block'},400)
		
		elif event['gist'] == 'compliant':
			speech.consider(life,event['from'],'compliant')
		
		elif event['gist'] == 'intimidate':
			if event_delay(event,60):
				continue
			
			lfe.say(life,'I\'ll shoot if you come any closer.')
			communicate(life,'intimidate_with_weapon',target=event['from'])
		
		elif event['gist'] == 'drop_everything':
			if life == event['target'] and brain.get_flag(life, 'surrendered'):
				lfe.drop_all_items(life)
		
		elif event['gist'] == 'intimidate_with_weapon':
			if event_delay(event,60):
				continue
			
			#TODO: We should also use sounds (reloading, etc) to confirm
			#if the ALife is telling the truth.
			_lying = True
			
			for item in [lfe.get_inventory_item(event['from'],item) for item in check_snapshot(life,event['from'])['visible_items']]:
				if item['type'] == 'gun':
					_lying = False
			
			if _lying:
				lfe.say(life,'I know you don\'t have a gun.')
		
		elif event['gist'] == 'confidence':
			logging.debug('%s realizes %s is no longer afraid!' % (' '.join(life['name']),' '.join(event['from']['name'])))
			speech.consider(life,event['from'],'confidence')

		elif event['gist'] == 'greeting':
			if event_delay(event, 30):
				continue
			
			if not speech.has_sent(life, event['from'], 'greeting'):
				speech.communicate(life, 'greeting', matches=[{'id': event['from']['id']}])
				speech.send(life, event['from'], 'greeting')
				lfe.say(life, 'Hello there, traveler!')
			
			if not speech.has_received(life, event['from'], 'greeting'):
				speech.receive(life, event['from'], 'greeting')

		elif event['gist'] == 'insult':
			if event_delay(event, 20):
				continue

			if speech.consider(life, event['from'], 'insulted'):
				speech.communicate(life, 'insult', target=event['from'])
				lfe.say(life, 'You\'re a jerk!')
		
		elif event['gist'] == 'get_chunk_info':
			if event_delay(event, 60):
				continue

			if speech.has_sent(life, event['from'], 'get_chunk_info'):
				continue

			if not speech.has_received(life, event['from'], 'get_chunk_info'):
				speech.communicate(life, 'get_chunk_info', target=event['from'])
				speech.send(life, event['from'], 'no_chunk_info')
				lfe.say(life, 'I\'m new around here, sorry!')
		
		elif event['gist'] == 'share_chunk_info':
			if event_delay(event, 20):
				continue

			if 'chunk_key' in event:
				maps.refresh_chunk(event['chunk_key'])
				judgement.judge_chunk(life, event['chunk_key'])
				lfe.memory(life, 'heard about a chunk', target=event['from']['id'])

		elif event['gist'] == 'share_item_info':
			if event_delay(event, 20):
				continue

			if brain.has_remembered_item(life, event['item']['item']):
				print 'Already know about this item'
			else:
				lfe.memory(life, 'heard about an item',
					item=event['item']['item']['uid'],
					target=event['from']['id'])
				brain.remember_item_secondhand(life, event['from'], event['item'])
		
		elif event['gist'] == 'share_camp_info':
			if event_delay(event, 30):
				#TODO: This is only a PoC. The ALife stops to interpret the information.
				lfe.clear_actions(life)
				continue
			
			if not camps.has_discovered_camp(life, event['camp']):
				camps.discover_camp(life, event['camp'])
				
				#TODO: Judge and respond?
				lfe.memory(life, 'heard about camp',
					camp=event['camp']['id'],
					target=event['from']['id'])
		
		elif event['gist'] == 'welcome_to_camp':
			if event_delay(event, 20):
				continue
			
			if not speech.has_received(life, event['from'], 'welcome_to_camp'):
				lfe.say(life, 'It\'s good to be here.')
				speech.receive(life, event['from'], 'welcome_to_camp')
		
		elif event['gist'] == 'appear_friendly':			
			lfe.memory(life, 'friendly',
				target=event['from']['id'])
		
		elif event['gist'] == 'appear_hostile':			
			lfe.memory(life, 'hostile',
				target=event['from']['id'])
		
		elif event['gist'] == 'under_attack':
			if not brain.knows_alife(life, event['attacker']):
				brain.meet_alife(life, event['attacker'])
			
			_target = brain.knows_alife(life, event['attacker'])
			
			if lfe.get_memory(life, matches={'target': event['attacker']['id'], 'text': 'friendly'}):
				lfe.memory(life, 'traitor',
					target=event['attacker']['id'])
				lfe.say(life, 'You no-good traitor!')
			
			lfe.memory(life, 'hostile',
				target=event['attacker']['id'])
			
			#TODO: Radio back and ask where the target is (randomly have the sending ALife leave this info out so we have to ask)
			if not 'location' in event and not speech.has_sent(life, event['from'], 'get_alife_location'):
				speech.communicate(life,
					'get_alife_location',
					alife=event['attacker'],
					matches=[{'id': event['from']['id']}])
				lfe.say(life, 'Where is he?')
			elif 'location' in event:
				_target['last_seen_at'] = event['attacker']['pos'][:]
		
		elif event['gist'] == 'get_alife_location':
			_target = brain.knows_alife(life, event['alife'])
			
			#speech.send(life, event['from'], 'alife_location', alife=event['alife'], location=_target['last_seen_at'])
			speech.communicate(life,
				'alife_location',
				alife=event['alife'],
				location=_target['last_seen_at'][:],
				matches=[{'id': event['from']['id']}])
		
		elif event['gist'] == 'alife_location':
			_target = brain.knows_alife(life, event['alife'])
			
			#TODO: Trust should play a factor here (and also when we ask for the location too)
			_target['last_seen_at'] = event['location']
		
		else:
			logging.warning('Unhandled ALife context: %s' % event['gist'])
		
		life['heard'].remove(event)

def event_delay(event,time):
	if event['age'] < time:
		event['age'] += 1
		
		return True
	
	return False
