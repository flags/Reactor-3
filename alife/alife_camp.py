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
	
	if life['state'] in ['hiding', 'hidden', 'working', 'needs']:
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
		
		if not life['id'] == _info['founder']:
			if not brain.knows_alife_by_id(life, _info['founder']):
				if not lfe.get_memory(life, matches={'text': 'where is target', 'target': _info['founder']}):
					lfe.memory(life, 'where is target', target=_info['founder'], question=True)
				
			elif not life['job']:
				if not lfe.get_memory(life, matches={'text': 'no jobs', 'target': _info['founder']}):
					_j = jobs.create_job(life, 'get camp job')
					jobs.add_detail_to_job(_j, 'target', _info['founder'])
					jobs.add_job_task(_j, 'find alife', callback=movement.find_alife, required=True)
					jobs.add_job_task(_j, 'ask for job', callback=jobs.ask_for_job, required=True)
					jobs.add_job_candidate(_j, life)
					jobs.process_job(_j)
		else:
			#TODO: Create jobs here?
			pass
			
	else:		
		if not lfe.get_memory(life, matches={'text': 'wants_founder_info', 'camp': _camp['id']}):
			lfe.memory(life, 'wants_founder_info', camp=_camp['id'], question=True)
	
	#if _info['estimated_population']<2:
		
