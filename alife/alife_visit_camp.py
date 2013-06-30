from globals import *

import life as lfe

import judgement
import camps

import logging

STATE = 'visiting camp'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED

	if not 'INTELLIGENT' in life['life_flags']:
		return False	
	
	if not judgement.is_safe(life):
		return False	
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	#Founding didn't work out...
	if not life['known_camps'] or life['camp']:
		return False
	
	return RETURN_VALUE

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_camp = camps.get_nearest_known_camp(life)
	
	if camps.is_in_camp(life, _camp):
		lfe.create_question(life,
			'wants_founder_info',
			{'camp': _camp['id']},
			lfe.get_memory,
			{'text': 'heard_about_camp', 'camp': _camp['id'], 'founder': '*'})
		
		if lfe.get_memory(life, matches={'text': 'heard_about_camp', 'camp': _camp['id'], 'founder': '*'}):
			lfe.create_question(life,
				'ask_to_join_camp',
				{'camp': _camp['id']},
				lfe.get_memory,
				[{'text': 'join_camp', 'camp': _camp['id'], 'founder': '*'},
				{'text': 'deny_from_camp', 'camp': _camp['id'], 'founder': '*'}],
				match_gist_only=True,
				answer_all=True)
			
	
	#life['camp'] = _camp['id']
	print 'lookan'
