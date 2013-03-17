import life as lfe

import speech
import brain

import logging

def listen(life):	
	for event in life['heard'][:]:
		if not event['from']['id'] in life['know']:
			pass
			#logging.warning('%s does not know %s!' % (' '.join(event['from']['name']),' '.join(life['name'])))
		
		if event['gist'] == 'surrender':
			if speech.consider(life,event['from'],'surrendered'):
				logging.debug('%s realizes %s has surrendered.' % (' '.join(life['name']),' '.join(event['from']['name'])))
				
				speech.communicate(life,'stand_still',target=event['from'])
		
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
			if event_delay(event, 20):
				continue
			
			if not speech.has_answered(life, event['from'], 'greeting'):
				speech.communicate(life, 'greeting', target=event['from'])
				speech.answer(life, event['from'], 'greeting')
				lfe.say(life, 'Hello there, traveler!')

		elif event['gist'] == 'insult':
			if event_delay(event, 20):
				continue

			if speech.consider(life, event['from'], 'insulted'):
				speech.communicate(life, 'insult', target=event['from'])
				lfe.say(life, 'You\'re a jerk!')
		
		elif event['gist'] == 'ask_for_chunk_info':
			if event_delay(event, 20):
				continue

			if speech.consider(life, event['from'], 'asked_for_chunk_info'):
				#speech.communicate(life, 'ask_for_chunk_info', target=event['from'])
				print 'derpppppppppppppp'
				lfe.say(life, 'I haven\'t seen anything interesting lately.')
				speech.communicate(life, 'ask_for_chunk_info', target=event['from'])
		
		life['heard'].remove(event)

def event_delay(event,time):
	if event['age'] < time:
		event['age'] += 1
		
		return True
	
	return False
