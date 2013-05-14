from globals import *

import life as lfe

import references
import judgement
import movement
import speech
import brain
import camps
import jobs
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
	
	#Start figuring out what's going on inside the camp
	#We're asking ourselves what needs to be done? Is someone in charge? Do we need supplies?
	#NOTE: We've already been attracted here. Think twice before abandoning...
	_info = camps.get_camp_info(life, _camp)
	
	if not _info['founder']==-1:
		if not camps.is_in_camp(life, _camp):
			_closest_key =  references.find_nearest_key_in_reference(life, _camp['reference'])
			_chunk = maps.get_chunk(_closest_key)
			
			lfe.clear_actions(life)
			lfe.add_action(life,{'action': 'move',
				'to': random.choice(_chunk['ground'])},
				200)
			return False
		
		_can_actually_help = []
		for can_help_find in lfe.get_memory(life, matches={'camp': _camp['id'], 'text': 'help find founder'}):
			if not lfe.get_memory(life, matches={'target': can_help_find['target'], 'camp': _camp['id'], 'text': 'told about founder'}):
				_can_actually_help.append(can_help_find['target'])
		
		#TODO: Score these
		if _can_actually_help:
			#This should always return something
			_target = brain.knows_alife_by_id(life, _can_actually_help.pop())
			
			if not lfe.get_memory(life, matches={'target': can_help_find['target'], 'camp': _camp['id'], 'text': 'go tell about founder'}):
				lfe.memory(life, 'go tell about founder',
					camp=_camp['id'],
					target=_target['life']['id'])
					
				#This will be a very general job that give another alife a specific memory
				_j = jobs.create_job(life, 'give information')
				jobs.add_detail_to_job(_j, 'say', {'gist': 'camp_founder',
					'founder': _info['founder'],
					'camp': _camp['id'],
					'target': _target['life']['id']})
				jobs.add_detail_to_job(_j, 'target', _target['life']['id'])
				jobs.add_job_task(_j, 'find alife', callback=movement.find_alife_and_say, required=True)
				jobs.add_job_candidate(_j, life)
				jobs.process_job(_j)
			
	else:		
		#Try to find out who he is...
		speech.announce(life, 'who_is_founder', camp=_camp['id'])
		
		#_possible_people_to_ask = []
		#for target in speech.get_announce_list(life):
		#	#TODO: In this case we'll be approached (maybe) by the ALife if they find the info...
		#	if lfe.get_memory(life, matches={'target': target['id'], 'camp': _camp['id'], 'text': 'dont know founder'}):
		#		continue
		#	
		#	if lfe.get_memory(life, matches={'target': target['id'], 'camp': _camp['id'], 'text': 'heard about camp', 'founder': '*'}):
		#		continue
		#	
		#	speech.unsend(life, target, 'who_is_founder')
		#	_possible_people_to_ask.append(target)
		#
		#if _possible_people_to_ask:
		#	#TODO: Who to see first?
		#	_found = False
		#	for target in _possible_people_to_ask:
		#		_target = brain.knows_alife_by_id(life, target['id'])
		#	
		#		if not life['pos'][:2] == _target['last_seen_at'][:2]:
		#			_found = True
		#			break					
		#	
		#	#TODO: Job needed here
		#	if _found:
		#		lfe.clear_actions(life)
		#		lfe.add_action(life,{'action': 'move',
		#			'to': _target['last_seen_at'][:2]},
		#			200)
		#else:
		if not lfe.get_memory(life, matches={'text': 'wants_founder_info', 'camp': _camp['id']}):
			lfe.memory(life, 'wants_founder_info', camp=_camp['id'], question=True)

		#print 'missed announce',speech.who_missed_announce(life, 'who_is_founder')
		#We don't have a founder still
		#for target in speech.who_missed_announce(life, 'who_is_founder'):
		#speech.unsend(life, LIFE[target], 'who_is_founder')		
	
	#if _info['estimated_population']<2:
		
