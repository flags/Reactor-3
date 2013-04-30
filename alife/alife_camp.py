from globals import *

import life as lfe

import references
import judgement
import movement
import speech
import camps
import maps

import logging
import random

STATE = 'camping'
INITIAL_STATES = ['idle', 'hidden']
CHECK_STATES = INITIAL_STATES[:]
CHECK_STATES.append(STATE)
ENTRY_SCORE = 0

def calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen):
	_score = 0
	
	for entry in targets_seen:
		_score += entry['score']
	
	return _score

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED
	
	if life['state'] in ['hiding', 'hidden', 'working']:
		return False
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	if calculate_safety(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen) < ENTRY_SCORE:
		return False

	if not life['camp']:
		return False

	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	_camp = life['known_camps'][life['camp']]
	if not camps.is_in_camp(life, _camp):
		_closest_key =  references.find_nearest_key_in_reference(life, _camp['reference'])
		_chunk = maps.get_chunk(_closest_key)
		
		lfe.clear_actions(life)
		lfe.add_action(life,{'action': 'move',
			'to': random.choice(_chunk['ground'])},
			200)
		return False
	
	#Start figuring out what's going on inside the camp
	#We're asking ourselves what needs to be done? Is someone in charge? Do we need supplies?
	#NOTE: We've already been attracted here. Think twice before abandoning...
	_info = camps.get_camp_info(life, _camp)
	
	if _info['founder']:
		print 'can help!',_info['founder']
		#print life['name'],_camp['id'],lfe.get_memory(life, matches={'text': 'help find founder'})
		#for can_help_find in lfe.get_memory(life, matches={'camp': _camp['id'], 'text': 'help find founder'}):
		#	print can_help_find['target']
	else:
		#print 'Looking for founder...'
		
		#Try to find out who he is...
		speech.announce(life, 'who_is_founder', camp=_camp['id'])
		
		#if lfe.ticker(life, 'who_is_founder', 100):
		for target in speech.get_announce_list(life):
			#TODO: In this case we'll be approached (maybe) by the ALife if they find the info...
			if lfe.get_memory(life, matches={'target': target['id'], 'camp': _camp['id'], 'text': 'dont know founder'}):
				continue
			
			if lfe.get_memory(life, matches={'target': target['id'], 'camp': _camp['id'], 'text': 'heard about camp', 'founder': '*'}):
				continue
			
			speech.unsend(life, target, 'who_is_founder')
		#print 'missed announce',speech.who_missed_announce(life, 'who_is_founder')
		#We don't have a founder still
		#for target in speech.who_missed_announce(life, 'who_is_founder'):
		#speech.unsend(life, LIFE[target], 'who_is_founder')		
	
	#if _info['estimated_population']<2:
		
