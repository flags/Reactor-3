import life as lfe

import judgement
import speech
import combat
import brain
import camps
import maps
import jobs

import logging

def listen(life):	
	for event in life['heard'][:]:
		if not event['from']['id'] in life['know']:
			pass
			#logging.warning('%s does not know %s!' % (' '.join(event['from']['name']),' '.join(life['name'])))
		
		if event_delay(event, 20):
			return False
		
		if not brain.knows_alife(life, event['from']):
			brain.meet_alife(life, event['from'])
			
			logging.info('%s learned about %s via listen.' % (' '.join(life['name']), ' '.join(event['from']['name'])))
		
		if event['gist'] == 'job':
			print 'Got job:', event['job']['gist']
			jobs.add_job_candidate(event['job'], life)
			jobs.process_job(event['job'])
		
		elif event['gist'] == 'surrender':
			_found_related_job = False
			for _j in jobs.find_jobs_of_type('surrender'):
				if jobs.alife_is_factor_of_job(event['from'], _j):
					_found_related_job = True
					break
			
			if not _found_related_job:
				_j = jobs.create_job(life, 'surrender')
				#jobs.add_job_callback(_j, )
				jobs.add_job_factor(_j, 'alife', event['from'])
				jobs.add_job_task(_j, 'disarm', callback=combat.disarm)
				jobs.add_job_task(_j, 'guard', callback=combat.guard, depends_on='disarm')
				jobs.add_job_candidate(_j, life)
				jobs.announce_job(life, _j)
				jobs.process_job(_j)
					
			#if not speech.has_received(life, event['from'], 'surrender'):
			#	speech.receive(life, event['from'], 'surrender')
			#	lfe.memory(life, 'surrendered', target=event['from']['id'])
			#	speech.announce(life, 'target_surrendered', target=event['from'])
		
		elif event['gist'] == 'target_surrendered':
			if not brain.knows_alife(life, event['target']):
				brain.meet_alife(life, event['target'])
			
			print life['name'],'Got secondhand knowledge of a surrender'
			lfe.memory(life, 'surrendered', target=event['from']['id'])
			brain.flag_alife(life, event['target'], 'not_handling_surrender', value=event['from'])
		
		elif event['gist'] == 'dropped_demanded_item':
			if brain.knows_alife(life, event['from']):
				#brain.flag_alife(life, event['from'], 'dropped_demanded_item')
				
				if jobs.alife_is_factor_of_any_job(event['from']):
					print 'yeah!'
			#else:
			#	print life['name'],'dont know this guy'
		
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
		
		elif event['gist'] == 'greeting':
			if event_delay(event, 30):
				continue
			
			if not speech.has_sent(life, event['from'], 'greeting'):
				speech.communicate(life, 'greeting', matches=[{'id': event['from']['id']}])
				speech.send(life, event['from'], 'greeting')
				lfe.say(life, 'Hello there, traveler!')
			
			if not speech.has_received(life, event['from'], 'greeting'):
				speech.receive(life, event['from'], 'greeting')
		
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
			
			speech.communicate(life,
				'alife_location',
				alife=event['alife'],
				location=_target['last_seen_at'][:],
				matches=[{'id': event['from']['id']}])
		
		elif event['gist'] == 'alife_location':
			_target = brain.knows_alife(life, event['alife'])
			
			#TODO: Trust should play a factor here (and also when we ask for the location too)
			_target['last_seen_at'] = event['location']
		
		elif event['gist'] == 'target_needs_disarmed':
			if not brain.knows_alife(life, event['alife']):
				brain.meet_alife(life, event['alife'])
			
			#TODO: In the future we should consider giving this task to another ALife
			#_target = brain.knows_alife(life, event['alife'])['score']
			logging.warning('target_needs_disarmed: Needs handling code.')
		
		else:
			logging.warning('Unhandled ALife context: %s' % event['gist'])
		
		life['heard'].remove(event)

def event_delay(event,time):
	if event['age'] < time:
		event['age'] += 1
		
		return True
	
	return False
