#This is intended to be an example of how the new ALife
#system works.
from globals import *

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
	return STATE_UNCHANGED

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	#TODO: Add these two values to an array called PANIC_STATES
	if not life['state'] in ['hiding', 'hidden'] and alife_seen:
		_talk_to = [alife['who'] for alife in alife_seen if not 'greeted' in alife['who']['consider']]
		
		if len(_talk_to)>=2:
			for alife in _talk_to:
				print alife
				speech.communicate(life, 'greeting', target=alife)
		elif _talk_to:
			speech.communicate(life, 'greeting', target=_talk_to[0]['life'])
			
			
