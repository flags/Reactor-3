from globals import *

import life as lfe

import action

import traceback
import logging
import sys

def has_goal(life, name, goal):
	return [g for g in life['goals'].values() if g['goal'] == goal and g['name'] == name]

def has_active_goals(life):
	return [g for g in life['goals'].values() if not g['complete']]

def get_goal_via_id(life, goal_id):
	if goal_id in life['goals']:
		return life['goals'][goal_id]
	
	raise Exception('%s has no goal with ID `%s`' % (' '.join(life['name']), goal_id))

def get_criteria(life, goal_id, criteria_id):
	_goal = get_goal_via_id(life, goal_id)
	
	if criteria_id in _goal['criteria']:
		return _goal['criteria'][criteria_id]
	
	raise Exception('%s has no goal with criteria ID `%s`' % (' '.join(life['name']), criteria_id))

def add_goal(life, name, goal):
	if has_goal(life, name, goal):
		return False
	
	_goal = {'name': name,
		'goal': goal,
		'criteria': {},
		'id': WORLD_INFO['goalid'],
		'cid': 1,
		'flags': {},
		'complete_on_answer': [],
		'complete': False}
	life['goals'][_goal['id']] = _goal
	
	WORLD_INFO['goalid'] += 1
	logging.debug('%s added goal: %s' % (' '.join(life['name']), name))
	
	return _goal['id']

def flag(life, goal_id, flag, value):
	_goal = get_goal_via_id(life, goal_id)
	
	_goal['flags'][flag] = value

def get_flag(life, goal_id, flag):
	_goal = get_goal_via_id(life, goal_id)
	
	if not flag in _goal['flags']:
		raise Exception('%s: group \'%s\' does not have flag: %s' % (' '.join(life['name']), _goal['name'], flag))
	
	return _goal['flags'][flag]

def add_criteria(life, goal_id, kind, criteria):
	_goal = get_goal_via_id(life, goal_id)
	
	criteria['id'] = _goal['cid']
	criteria['sub_criteria'] = []
	criteria['type'] = kind
	_goal['criteria'][criteria['id']] = criteria
	_goal['cid'] += 1
	
	logging.debug('%s added criteria to goal \'%s\': %s' % (' '.join(life['name']), _goal['name'], criteria['type']))
	
	return criteria['id']

def add_action(life, goal_id, action):
	_goal = get_goal_via_id(life, goal_id)
	
	return add_criteria(life, goal_id, 'action', {'action': action})

def add_task(life, goal_id, callback, **kwargs):
	_goal = get_goal_via_id(life, goal_id)
	
	return add_criteria(life, goal_id, 'task', {'args': kwargs})

def add_memory(life, goal_id, memory):
	_goal = get_goal_via_id(life, goal_id)
	
	return add_criteria(life, goal_id, 'memory', {'matching': memory})

def filter_criteria(life, goal_id, criteria_id, callback):
	_goal = get_goal_via_id(life, goal_id)
	
	_criteria = get_criteria(life, goal_id, criteria_id)
	_criteria['sub_criteria'].append({'filter': callback})
	
	logging.debug('%s added sub-criteria filter to \'%s\' in goal \'%s\'' % (' '.join(life['name']), criteria_id, goal_id))

def match_criteria(life, goal_id, criteria_id, callback, **kwargs):
	_goal = get_goal_via_id(life, goal_id)
	
	_criteria = get_criteria(life, goal_id, criteria_id)
	_criteria['sub_criteria'].append({'match': callback, 'args': kwargs})
	
	logging.debug('%s added sub-criteria match to \'%s\' in goal \'%s\'' % (' '.join(life['name']), criteria_id, goal_id))

def match_action(life, goal_id, criteria_id, action):
	_goal = get_goal_via_id(life, goal_id)
	
	_criteria = get_criteria(life, goal_id, criteria_id)
	_criteria['sub_criteria'].append({'match_action': action})
	
	logging.debug('%s added sub-criteria match_action to \'%s\' in goal \'%s\'' % (' '.join(life['name']), criteria_id, goal_id))

def process_goals(life):
	for goal in life['goals'].keys():
		_goal = get_goal_via_id(life, goal)
		
		if _goal['complete']:
			continue
		
		for question in _goal['complete_on_answer']:
			if lfe.get_memory_via_id(life, question)['answered']:
				print 'DELETED GOAL!' * 100
				_goal['complete'] = True
				break
		
		if _process_goal(life, goal):
			print 'DELETED GOAL!' * 100
			_goal['complete'] = True
			
			print 'FINISHED GOAL' * 50

def _process_goal(life, goal_id):
	_goal = get_goal_via_id(life, goal_id)
	
	for criteria in _goal['criteria'].values():
		criteria['result'] = None
		
		if criteria['type'] == 'memory':
			criteria['result'] = lfe.get_memory(life, matches=criteria['memory'])
			
		elif criteria['type'] == 'action':
			criteria['result'] = action.execute(criteria['action'])
			if criteria['result'] == MISSING_KEY_IN_ACTION:
				traceback.print_exc(file=sys.stdout)
				raise Exception('Key missing: %s' % criteria['action'])
	
		if criteria['result']:
			_process = process_criteria(life, goal_id, criteria['id'], criteria['result'])
			criteria['result'] = _process
			
			if not criteria['result']:
				print 'Goal not met', life['name'], criteria
				continue
		else:
			if not meet_criteria(life, goal_id, criteria['id']):
				continue
	
	return True

def meet_criteria(life, goal_id, criteria_id):
	""" Perform actions that will generate criteria """
	_goal = get_goal_via_id(life, goal_id)
	_criteria = get_criteria(life, goal_id, criteria_id)
	
	if 'match' in _criteria:
		return _criteria['match'](life, *_criteria['args'])
	elif 'match_action' in _criteria:
		return action.execute(_criteria['match_action'])
	elif 'filter' in _criteria:
		return [entry for entry in result if _criteria['filter'](life, entry)]


def process_criteria(life, goal_id, criteria_id, result):
	""" Checks result of goal """
	_goal = get_goal_via_id(life, goal_id)
	_criteria = get_criteria(life, goal_id, criteria_id)
	
	for sub_criteria in _criteria['sub_criteria']:
		if 'match' in sub_criteria:
			return sub_criteria['match'](life, **sub_criteria['args'])
		elif 'match_action' in sub_criteria:
			return action.execute(sub_criteria['match_action'])
		elif 'filter' in sub_criteria:
			return [entry for entry in result if sub_criteria['filter'](life, entry)]

def complete_on_answer(life, goal_id, question_id):
	_goal = get_goal_via_id(life, goal_id)
	_goal['complete_on_answer'].append(question_id)
