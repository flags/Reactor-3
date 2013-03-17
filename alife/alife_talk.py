from globals import *
import life as lfe

import judgement
import movement
import speech

import logging

ENTRY_SCORE = 0

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#Note: We don't want to change the state because we're running this module alongside
	#other modules that will (most likely) be changing states for us...
	#Instead we're going to read the current state and react accordingly via flipping
	#life[['flags'] and spawning conversations based on that (and the state of course).
	#The main focus is to provide effective output rather than a lot of it, so the less
	#conversations we spawn the better.
	if not alife_seen:
		return False
	
	if life['state'] in ['hiding', 'hidden']:
		return False
	
	return STATE_UNCHANGED

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#TODO: Add these two values to an array called PANIC_STATES
	if not alife_seen:
		return False
	
	for ai in [alife['who'] for alife in alife_seen]:		
		#What's our relationship with them?
		if speech.has_asked(life, ai['life'], 'greeting'):
			#if not 'greeted' in ai['consider']:
			#	continue
			pass
			
			#if 'asked_for_chunk_info' in ai['consider']:
			#	pass
			#else:
			#	speech.communicate(life, 'ask_for_chunk_info', target=ai['life'])
			#	speech.consider(life, ai['life'], 'asked_for_chunk_info')
		else:
			if not speech.discussed(life, ai['life'], 'greeting'):
				print life['name']
				speech.communicate(life, 'greeting', matches=[{'id': ai['life']['id']}])
				speech.ask(life, ai['life'], 'greeting')
	
	#if len(_talk_to)>=2:
	#	for alife in _talk_to:
	#		speech.communicate(life, 'greeting', target=alife)
	#		speech.has_considered(life, alife, 'greeted')
	#elif _talk_to:
	#	speech.communicate(life, 'greeting', target=_talk_to[0]['life'])
	#	speech.consider(life, _talk_to[0]['life'], 'tried_to_greet')	
