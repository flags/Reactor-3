from globals import *

import life as lfe

import action
import chunks
import goals

def conditions(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	return RETURN_SKIP

def tick(life, alife_seen, alife_not_seen, targets_seen, targets_not_seen, source_map):
	if lfe.execute_raw(life, 'discover', 'desires_shelter'):
		_g = goals.add_goal(life, 'find and take shelter')
		if _g:
			_c = goals.add_action(life, _g, action.make('return_key',
			                                            retrieve={'list': life['known_chunks'].keys()},
			                                            key='list',
			                                            life=life['id']), required=True)
			goals.filter_criteria_with_action(life, _g, _c,
			                                  action.make('filter',
			                                              life=life['id'],
			                                              retrieve={'goal_id': _g, 'criteria_id': _c},
			                                              store_retrieve_as='chunk_id',
			                                              function=chunks.get_flag,
			                                              arguments=action.make('return',
			                                                                    include={'flag': 'shelter'},
			                                                                    life=life['id'])))
			                                              
			#goals.filter_criteria_with_action(life, _g, _c,
		     #                                  action.make('filter',
		     #                                              life=life['id'],
		     #                                              retrieve={'goal_id': _g, 'criteria_id': _c},
		     #                                              store_retrieve_as='target_id',
		     #                                              function=lfe.can_ask,
		     #                                              arguments=action.make('return',
		     #                                                                    include={'question_id': _q},
		     #                                                                    life=life['id'])))
			#goals.filter_criteria(life, _g, _c, judgement.can_trust)
			#goals.filter_criteria(life, _g, _c, judgement.is_target_lost, invert=True)
			
			#goals.add_action(life, _g, action.make('track_alife',
		     #                                       life=life['id'],
		     #                                       retrieve={'goal_id': _g, 'criteria_id': _c},
		     #                                       add_to=goals.get_flag(life, _g, 'talk_to'),
		     #                                       filter_by=goals.get_flag(life, _g, 'talked_to')))
			#goals.filter_criteria_with_action(life, _g, _c, action.make('filter',
			#                                                            life=life['id'],
			#                                                            retrieve=))
			#goals.add_action(life, _g, action.make('ask',
		     #                                       life=life['id'],
		     #                                       retrieve={'list': goals.get_flag(life, _g, 'talk_to')},
		     #                                       add_to=goals.get_flag(life, _g, 'talked_to'),
		     #                                       question=_q))