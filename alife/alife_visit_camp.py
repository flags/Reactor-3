from globals import *

import life as lfe

import judgement
import brain
import camps
import stats

import logging

STATE = 'visiting camp'

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	RETURN_VALUE = STATE_UNCHANGED

	if life['state'] in ['combat', 'exploring', 'searching']:
		return False
	
	if not judgement.is_safe(life):
		return False	
	
	if not life['state'] == STATE:
		RETURN_VALUE = STATE_CHANGE
	
	return RETURN_SKIP

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):	
	_camp = camps.get_nearest_known_camp(life)
	
	if not _camp:
		return False
	
	if not stats.desires_to_join_camp(life, _camp['id']):
		return False
	
	if camps.is_in_camp(life, _camp):
		print life['name'],'IN CAMP AND WANTS TO JOIN'
		lfe.create_question(life,
			'wants_founder_info',
			{'camp': _camp['id']},
			lfe.get_memory,
			{'camp': _camp['id'], 'founder': '*'})
		
		if lfe.get_memory(life, matches={'camp': _camp['id'], 'founder': '*'}):
			lfe.create_question(life,
				'ask_to_join_camp',
				{'camp': _camp['id']},
				lfe.get_memory,
				[{'text': 'join_camp', 'camp': _camp['id'], 'founder': '*'},
				{'text': 'deny_from_camp', 'camp': _camp['id'], 'founder': '*'}],
				match_gist_only=True,
				answer_all=True)
	else:
		print life['name'],'NOT IN CAMP AND WANTS TO JOIN'
		_founder = camps.knows_founder(life, _camp['id'])
		if _founder:
			if not brain.get_impression(life, _founder, 'camp'):
				brain.add_impression(life, _founder, 'camp', {'influence': 25})
				print 'INFLUENCE!!!!!!'*10
			else:
				print 'ALREADY HAS IMPRESSION'
		else:
			print 'does not know founder'
			if not life['state'] == 'working':
				_q = lfe.create_question(life,
					'wants_founder_info',
					{'camp': _camp['id']},
					lfe.get_memory,
					{'camp': _camp['id'], 'founder': '*'})
				
				#if not life['state'] == 'working':
				#	lfe.track_target(life, 
			
				camps.investigate(life, _camp['id'], _q)
	
