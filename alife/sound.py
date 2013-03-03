def listen(life):
	for event in life['heard'][:]:
		if not str(event['from']['id']) in life['know']:
			logging.warning('%s does not know %s!' % (' '.join(event['from']['name']),' '.join(life['name'])))
		
		if event['gist'] == 'surrender':
			if consider(life,event['from'],'surrendered'):
				logging.debug('%s realizes %s has surrendered.' % (' '.join(life['name']),' '.join(event['from']['name'])))
				
				communicate(life,'stand_still',target=event['from'])
		
		elif event['gist'] == 'resist':
			if life == event['target']:
				if consider(life, event['from'], 'resist'):
					logging.debug('%s realizes %s is resisting.' % (' '.join(life['name']),' '.join(event['from']['name'])))
		
		elif event['gist'] == 'free_to_go':
			if life == event['target']:
				lfe.create_and_update_self_snapshot(event['from'])
				unconsider(life,event['from'],'surrender')
		
		elif event['gist'] == 'comply':
			#TODO: Judge who this is coming from...
			if life == event['target']:
				communicate(life,'surrender')
		
		elif event['gist'] == 'demand_drop_item':
			if life == event['target']:
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
			if life == event['target']:
				lfe.add_action(life,{'action': 'block'},1000)
				lfe.clear_actions(life)
				flag(life, 'surrendered')
		
		elif event['gist'] == 'compliant':
			if life == event['target']:
				consider(life,event['from'],'compliant')
		
		elif event['gist'] == 'intimidate':
			if event_delay(event,60):
				continue
			
			#Here we go...
			#This is the first *real* chance to make the ALife
			#just that much more complex...
			#We can make them lie about their current situation
			#to intimiate the person right back
			
			if life == event['target']:
				lfe.say(life,'I\'ll shoot if you come any closer.')
				communicate(life,'intimidate_with_weapon',target=event['from'])
		
		elif event['gist'] == 'drop_everything':
			if life == event['target'] and get_flag(life, 'surrendered'):
				lfe.drop_all_items(life)
				unflag(life, 'surrendered')
		
		elif event['gist'] == 'intimidate_with_weapon':
			if event_delay(event,60):
				continue
			
			#TODO: We should also use sounds (reloading, etc) to confirm
			#if the ALife is telling the truth.
			if life == event['target']:
				_lying = True
				
				for item in [lfe.get_inventory_item(event['from'],item) for item in check_snapshot(life,event['from'])['visible_items']]:
					if item['type'] == 'gun':
						_lying = False
				
				if _lying:
					lfe.say(life,'I know you don\'t have a gun.')
					#communicate(life,
		
		elif event['gist'] == 'confidence':
			logging.debug('%s realizes %s is no longer afraid!' % (' '.join(life['name']),' '.join(event['from']['name'])))
			consider(life,event['from'],'confidence')

		elif event['gist'] == 'greeting':
			if event_delay(event, 60):
				continue

			if life == event['target']:
				if not has_considered(life, event['from'], 'greeting'): 
					communicate(life, 'greeting', target=event['from'])
					lfe.say(life, 'Hello there, traveler!')
				else:
					print 'We past this dawg!!!'

		elif event['gist'] == 'insult':
			if event_delay(event, 30):
				continue

			if life == event['target']:
				if not has_considered(life, event['from'], 'insult'):
					communicate(life, 'insult', target=event['from'])
					lfe.say(life, 'You\'re a jerk!')
		
		life['heard'].remove(event)
