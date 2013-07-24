from globals import *

import life as lfe

import judgement
import movement
import action
import goals
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
		_founder = camps.knows_founder(life, _camp['id'])
		
		if _founder:
			#print 'Knows founder'
			pass
		else:
			#print 'does not know founder!' * 10
			_g = goals.add_goal(life, 'find founder', investigate=True)
			if _g:
				_q = lfe.create_question(life,
					'wants_founder_info',
					{'camp': _camp['id']},
					lfe.get_memory,
					{'text': 'heard_about_camp', 'camp': _camp['id'], 'founder': '*'})
				
				goals.flag(life, _g, 'talk_to', [])
				goals.flag(life, _g, 'talked_to', [])
				
				goals.complete_on_answer(life, _g, _q)
				
				_c = goals.add_action(life, _g, action.make('get_known_alife', life=life['id'], matching={'id': '*'}))
				goals.filter_criteria_with_action(life, _g, _c,
				                                  action.make('filter',
				                                              life=life['id'],
				                                              retrieve={'goal_id': _g, 'criteria_id': _c},
				                                              store_retrieve_as='target_id',
				                                              function=lfe.can_ask,
				                                              arguments=action.make('return',
				                                                                    include={'question_id': _q},
				                                                                    life=life['id'])))
				goals.filter_criteria(life, _g, _c, judgement.can_trust)
				goals.filter_criteria(life, _g, _c, judgement.is_target_lost, invert=True)
				
				goals.add_action(life, _g, action.make('track_alife',
				                                       life=life['id'],
				                                       retrieve={'goal_id': _g, 'criteria_id': _c},
				                                       add_to=goals.get_flag(life, _g, 'talk_to'),
				                                       filter_by=goals.get_flag(life, _g, 'talked_to')))
				#goals.filter_criteria_with_action(life, _g, _c, action.make('filter',
				#                                                            life=life['id'],
				#                                                            retrieve=))
				goals.add_action(life, _g, action.make('ask',
				                                       life=life['id'],
				                                       retrieve={'list': goals.get_flag(life, _g, 'talk_to')},
				                                       add_to=goals.get_flag(life, _g, 'talked_to'),
				                                       question=_q))
