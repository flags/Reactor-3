from globals import *
import life as lfe

import judgement
import movement
import speech
import brain

import logging

ENTRY_SCORE = 0

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#Note: We don't want to change the state because we're running this module alongside
	#other modules that will (most likely) be changing states for us...
	#Instead we're going to read the current state and react accordingly via flipping
	#life[['flags'] and spawning conversations based on that (and the state of course).
	#The main focus is to provide effective output rather than a lot of it, so the less
	#conversations we spawn the better.
	#if not alife_seen:
	#	return False
	
	if life['state'] in ['hiding', 'hidden']:
		return False
	
	return STATE_UNCHANGED

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#TODO: Add these two values to an array called PANIC_STATES
	#if not alife_seen:
	#	return False
	
	for ai in [alife['who'] for alife in alife_seen]:
		#print life['know'][ai['life']['id']]['asked'],life['know'][ai['life']['id']]['answered']
		#What's our relationship with them?
		if speech.has_asked(life, ai['life'], 'greeting'):
			if speech.has_asked(life, ai['life'], 'get_chunk_info'):
				pass
			else:
				if not speech.discussed(life, ai['life'], 'get_chunk_info'):
					speech.communicate(life,
						'get_chunk_info',
						say='Hello!',
						matches=[{'id': ai['life']['id']}])
					speech.ask(life, ai['life'], 'get_chunk_info')
		else:
			if not speech.discussed(life, ai['life'], 'greeting'):
				speech.communicate(life, 'greeting', say='Hello!', matches=[{'id': ai['life']['id']}])
				speech.ask(life, ai['life'], 'greeting')


	_visible_items = [life['know_items'][item] for item in life['know_items'] if not life['know_items'][item]['last_seen_time'] and not 'id' in life['know_items'][item]['item']]
	#_chunk_keys_of_visible_items = set(['%s,%s' % ((item['item']['pos'][0]/SETTINGS['chunk size'])*SETTINGS['chunk size'], (item['item']['pos'][1]/SETTINGS['chunk size'])*SETTINGS['chunk size']) for item in _visible_items])
	for ai in [life['know'][i] for i in life['know']]:
		if ai['score']<=0:
			continue

		for item in _visible_items:
			if  brain.has_shared_item_with(life, ai['life'], item['item']):
				continue

			_item_chunk_key = '%s,%s' % ((item['item']['pos'][0]/SETTINGS['chunk size'])*SETTINGS['chunk size'],
				(item['item']['pos'][1]/SETTINGS['chunk size'])*SETTINGS['chunk size'])

			speech.communicate(life,
				'share_item_info',
				item=brain.get_remembered_item(life, item['item']),
				matches=[{'id': ai['life']['id']}])

			speech.communicate(life,
				'share_chunk_info',
				chunk_key=_item_chunk_key,
				matches=[{'id': ai['life']['id']}])
			brain.share_item_with(life, ai['life'], item['item'])
			#speech.ask(life, ai['life'], 'share_chunk_info')

	#if len(_talk_to)>=2:
	#	for alife in _talk_to:
	#		speech.communicate(life, 'greeting', target=alife)
	#		speech.has_considered(life, alife, 'greeted')
	#elif _talk_to:
	#	speech.communicate(life, 'greeting', target=_talk_to[0]['life'])
	#	speech.consider(life, _talk_to[0]['life'], 'tried_to_greet')	
